"""
LSHW Parser Utility
Ported from the FastAPI app - same logic, just cleaner organization

This module parses lshw (Linux Hardware Lister) JSON output to extract:
- Device serial numbers
- CPU information
- RAM specifications
- Storage drives (with serial numbers, capacity, model)
- Hardware summary
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


def _walk_nodes(raw: Any):
    """
    Generator that walks through all nodes in the lshw JSON tree.
    lshw output is hierarchical with nested 'children' arrays.
    """
    if not isinstance(raw, dict):
        return
    stack = [raw]
    while stack:
        n = stack.pop()
        if not isinstance(n, dict):
            continue
        yield n
        kids = n.get("children")
        if isinstance(kids, list):
            stack.extend(kids)


def _looks_like_serial(s: str) -> bool:
    """
    Check if a string looks like a valid serial number.
    Filters out common placeholder values like "unknown", "0000000", etc.
    """
    if not s:
        return False
    s = s.strip()
    if len(s) < 6:
        return False
    bad = {
        "unknown",
        "none",
        "n/a",
        "na",
        "null",
        "0",
        "0000000",
        "00000000",
        "000000000",
        "not specified",
    }
    return s.lower() not in bad


def extract_serial(raw: dict) -> Optional[str]:
    """
    Extract the device serial number from lshw output.
    Looks at system, motherboard, and chassis serial numbers.
    Returns the first valid serial found.

    Args:
        raw: lshw JSON output (dict)

    Returns:
        Serial number string or None if not found
    """
    candidates: List[str] = []
    if not isinstance(raw, dict):
        return None

    # Check top-level serial and uuid
    for k in ("serial", "uuid"):
        v = raw.get(k)
        if isinstance(v, str) and _looks_like_serial(v):
            candidates.append(v)

    # Walk through all nodes looking for system-level serials
    for n in _walk_nodes(raw):
        cls = n.get("class")
        if cls in ("system", "bus", "motherboard", "bridge", "chassis"):
            v = n.get("serial")
            if isinstance(v, str) and _looks_like_serial(v):
                candidates.append(v)
        if cls == "system":
            v = n.get("uuid")
            if isinstance(v, str) and _looks_like_serial(v):
                candidates.append(v)

    return candidates[0] if candidates else None


def extract_cpu_info(raw: dict) -> Optional[str]:
    """
    Extract CPU information from lshw output.
    Returns a string like "Intel Corp. Intel(R) Core(TM) i5-8350U CPU @ 1.70GHz"

    Args:
        raw: lshw JSON output (dict)

    Returns:
        CPU description string or None if not found
    """
    if not isinstance(raw, dict):
        return None
    for n in _walk_nodes(raw):
        if n.get("class") == "processor":
            product = n.get("product")
            vendor = n.get("vendor")
            if isinstance(product, str) and product.strip():
                if isinstance(vendor, str) and vendor.strip():
                    return f"{vendor} {product}".strip()
                return product.strip()
    return None


def extract_system_info(raw: dict) -> Optional[dict]:
    """
    Extract the system-level vendor/product/serial information.
    Returns a dict like {"vendor": "...", "product": "...", "serial": "..."} or None.
    """
    if not isinstance(raw, dict):
        return None
    for n in _walk_nodes(raw):
        if n.get("class") == "system":
            vendor = n.get("vendor") or ""
            product = n.get("product") or ""
            serial = n.get("serial") or ""
            return {"vendor": vendor, "product": product, "serial": serial}
    return None


def extract_graphics(raw: dict) -> List[dict]:
    """
    Extract display/graphics adapters.
    Returns a list of dicts: [{"product": "...", "vendor": "...", "description": "..."}]
    """
    gpus: List[dict] = []
    if not isinstance(raw, dict):
        return gpus
    for n in _walk_nodes(raw):
        if n.get("class") == "display":
            product = n.get("product") or n.get("description") or ""
            vendor = n.get("vendor") or ""
            desc = n.get("description") or ""
            gpus.append({"product": product, "vendor": vendor, "description": desc})
    return gpus


def extract_network(raw: dict) -> List[dict]:
    """
    Extract network adapters (ethernet/wireless/bluetooth).
    Returns a list of dicts:
    [{"product": "...", "logicalname": "/dev/...", "mac": "...", "type": "wireless/ethernet/unknown"}]
    """
    nets: List[dict] = []
    if not isinstance(raw, dict):
        return nets
    for n in _walk_nodes(raw):
        if n.get("class") == "network":
            product = n.get("product") or n.get("description") or ""
            logical = n.get("logicalname") or ""
            serial = n.get("serial") or ""
            cfg = n.get("configuration") or {}
            # Try to infer type
            ntype = "unknown"
            # lshw may include 'wireless' in configuration or 'ip' keys for network interfaces
            if isinstance(cfg, dict):
                if (
                    cfg.get("wireless")
                    or cfg.get("wireless-info")
                    or cfg.get("driver")
                    and "wlan" in str(cfg.get("driver"))
                ):
                    ntype = "wireless"
                elif cfg.get("ip") or cfg.get("ip6"):
                    ntype = "ethernet"
            # fallback: check description/product text
            desc_text = (n.get("description") or "").lower()
            if "wireless" in desc_text or "wifi" in desc_text or "wlan" in desc_text:
                ntype = "wireless"
            if "ethernet" in desc_text or "network controller" in desc_text:
                ntype = ntype if ntype != "wireless" else ntype
            nets.append(
                {
                    "product": product,
                    "logicalname": logical,
                    "mac": serial,
                    "type": ntype,
                }
            )
    return nets


def extract_multimedia(raw: dict) -> dict:
    """
    Extract multimedia devices (webcam, microphone, audio).
    Returns: {"webcam": bool, "webcam_model": str, "audio": bool, "audio_model": str}
    """
    result = {"webcam": False, "webcam_model": "", "audio": False, "audio_model": ""}
    if not isinstance(raw, dict):
        return result
    for n in _walk_nodes(raw):
        if n.get("class") == "multimedia":
            product = (n.get("product") or n.get("description") or "").strip()
            desc = product.lower()
            # Detect webcam/camera
            if "camera" in desc or "webcam" in desc or "uvc" in desc:
                result["webcam"] = True
                if not result["webcam_model"]:
                    result["webcam_model"] = product
            # Detect microphone/audio/sound
            if "audio" in desc or "microphone" in desc or "sound" in desc:
                result["audio"] = True
                if not result["audio_model"]:
                    result["audio_model"] = product
    return result


def extract_battery(raw: dict) -> Optional[dict]:
    """
    Extract battery information for portable systems.
    Returns {"present": True, "product": "...", "vendor": "...", "capacity": int_bytes} or {"present": False}
    """
    if not isinstance(raw, dict):
        return {"present": False}
    for n in _walk_nodes(raw):
        nid = (n.get("id") or "").lower()
        desc = (n.get("description") or "").lower()
        if "battery" in nid or "battery" in desc:
            product = n.get("product") or n.get("description") or ""
            vendor = n.get("vendor") or ""
            size = n.get("size")
            capacity = None
            try:
                if isinstance(size, (int, float)):
                    capacity = int(size)
                elif isinstance(size, str) and size.isdigit():
                    capacity = int(size)
            except Exception:
                capacity = None
            return {
                "present": True,
                "product": product,
                "vendor": vendor,
                "capacity_bytes": capacity,
            }
    return {"present": False}


def parse_disks(raw: dict) -> List[Dict[str, Any]]:
    """
    Extract all disk drives from lshw output.
    For drives without valid serial numbers, generates a synthetic serial
    based on a hash of the drive characteristics (NOSERIAL-xxxxxxxxxxxxx).

    Args:
        raw: lshw JSON output (dict)

    Returns:
        List of dicts with keys: serial, logicalname, size_bytes, model
    """
    if not isinstance(raw, dict):
        return []

    disks: List[Dict[str, Any]] = []
    for n in _walk_nodes(raw):
        if n.get("class") != "disk":
            continue
        logical = n.get("logicalname")
        size = n.get("size")
        model = n.get("product") or n.get("description") or ""
        serial = n.get("serial")

        if isinstance(serial, str):
            serial = serial.strip()

        # If no valid serial, generate one based on drive characteristics
        if not _looks_like_serial(serial or ""):
            blob = json.dumps(
                {"logical": logical, "size": size, "model": model},
                sort_keys=True,
                default=str,
            ).encode("utf-8", errors="ignore")
            serial = "NOSERIAL-" + hashlib.sha1(blob).hexdigest()[:12]

        disks.append(
            {
                "serial": serial,
                "logicalname": logical if isinstance(logical, str) else "",
                "size_bytes": int(size) if isinstance(size, (int, float)) else None,
                "model": model,
            }
        )

    return disks


def format_bytes(num_bytes: int) -> str:
    """
    Convert bytes to human-readable format (KB, MB, GB, TB).

    Args:
        num_bytes: Number of bytes

    Returns:
        Human-readable string like "256.0 GB"
    """
    if not num_bytes:
        return "0 B"

    num = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def extract_basic_hw(raw: dict) -> Optional[dict]:
    """
    Extract a basic hardware summary from lshw output.
    Returns RAM and storage information in human-readable format.

    Args:
        raw: lshw JSON output (dict)

    Returns:
        Dict with keys 'ram' and 'storage', or None if no data found
        Example: {"ram": "16.0 GB", "storage": "256.0 GB TOSHIBA THNSFJ25 (SN 95CS1108TBZW)"}
    """
    if not isinstance(raw, dict):
        return None

    result: Dict[str, str] = {}

    # Extract RAM information
    total_bytes = 0
    sysmem = None

    # First, try to find "System Memory" entry (most accurate)
    for n in _walk_nodes(raw):
        if n.get("class") == "memory" and n.get("size"):
            desc = (n.get("description") or "").lower()
            if "system memory" in desc:
                try:
                    sysmem = int(n.get("size"))
                except Exception:
                    pass

    if sysmem:
        total_bytes = sysmem
    else:
        # Fall back to summing all memory (excluding cache)
        for n in _walk_nodes(raw):
            if n.get("class") == "memory" and n.get("size"):
                desc = (n.get("description") or "").lower()
                if "cache" in desc:
                    continue
                try:
                    total_bytes += int(n.get("size"))
                except Exception:
                    pass

    if total_bytes:
        result["ram"] = format_bytes(total_bytes)

    # Extract storage information
    disks = parse_disks(raw)
    if disks:
        labels = []
        for d in disks:
            parts = []
            if d.get("size_bytes"):
                parts.append(format_bytes(d["size_bytes"]))
            if d.get("model"):
                parts.append(d["model"])

            serial = d.get("serial")
            if serial:
                if serial.startswith("NOSERIAL-"):
                    parts.append("(no serial)")
                else:
                    parts.append(f"(SN {serial})")

            labels.append(" ".join(parts))

        result["storage"] = " + ".join(labels)

    return result or None


def parse_lshw_json(data: dict) -> dict:
    """
    Main entry point for parsing lshw JSON.
    Extracts all relevant information into a single summary dict.

    Args:
        data: lshw JSON output (dict)

    Returns:
        Dict with keys: device_serial, cpu_info, hw_summary, disks, system_info,
                        graphics, network, multimedia, battery, memory_slots, memory_total_bytes
    """
    # Extract basic pieces first
    device_serial = extract_serial(data)
    cpu_info = extract_cpu_info(data)
    hw_summary = extract_basic_hw(data)
    disks = parse_disks(data)
    system_info = extract_system_info(data)
    graphics = extract_graphics(data)
    network = extract_network(data)
    multimedia = extract_multimedia(data)
    battery = extract_battery(data)

    # Memory slots parsing:
    # Look for memory bank nodes and collect slot details.
    memory_slots: List[Dict[str, Optional[str]]] = []
    memory_total_bytes: Optional[int] = None

    # Try to find explicit system memory total first (system memory node)
    for n in _walk_nodes(data):
        if n.get("class") == "memory" and n.get("size"):
            desc = (n.get("description") or "").lower()
            # Prefer the top-level 'System Memory' entry for total if present
            if "system memory" in desc:
                try:
                    memory_total_bytes = int(n.get("size"))
                except Exception:
                    pass

    # Walk nodes to find memory banks / slots (class 'bank' or nodes with 'bank' in id/description)
    for n in _walk_nodes(data):
        cls = (n.get("class") or "").lower()
        nid = (n.get("id") or "").lower()
        desc = (n.get("description") or "").lower()

        # Heuristic: class 'bank' is common; also catch nodes with 'bank' in id/description
        if cls == "bank" or "bank" in nid or "bank" in desc:
            slot = n.get("slot") or n.get("id") or n.get("description") or ""
            size = n.get("size")
            vendor = n.get("vendor") or ""
            product = n.get("product") or ""
            serial = n.get("serial") or n.get("serial-number") or ""
            try:
                size_bytes = int(size) if isinstance(size, (int, float)) else None
            except Exception:
                size_bytes = None

            # Add human-readable size formatting
            size_human = None
            if size_bytes:
                size_human = format_bytes(size_bytes)

            memory_slots.append(
                {
                    "slot": slot,
                    "size_bytes": size_bytes,
                    "size_human": size_human,
                    "vendor": vendor,
                    "product": product,
                    "serial": serial,
                }
            )

    # If we didn't find a system memory total, derive it from slot sizes when possible
    if not memory_total_bytes:
        total = 0
        found_any = False
        for ms in memory_slots:
            if ms.get("size_bytes"):
                found_any = True
                total += ms["size_bytes"]
        if found_any:
            memory_total_bytes = total
        else:
            # As a last fallback, try to reuse hw_summary.ram if available (format: '16.0 GB')
            if hw_summary and isinstance(hw_summary, dict):
                ram_str = hw_summary.get("ram")
                if isinstance(ram_str, str) and ram_str.strip():
                    # Parse simple value like '16.0 GB'
                    try:
                        parts = ram_str.split()
                        value = float(parts[0])
                        unit = parts[1].upper() if len(parts) > 1 else "GB"
                        multiplier = 1
                        if unit == "KB":
                            multiplier = 1024
                        elif unit == "MB":
                            multiplier = 1024**2
                        elif unit == "GB":
                            multiplier = 1024**3
                        elif unit == "TB":
                            multiplier = 1024**4
                        memory_total_bytes = int(value * multiplier)
                    except Exception:
                        memory_total_bytes = None

    return {
        "device_serial": device_serial,
        "cpu_info": cpu_info,
        "hw_summary": hw_summary,
        "disks": disks,
        # Additional extracted info
        "system_info": system_info,
        "graphics": graphics,
        "network": network,
        "multimedia": multimedia,
        "battery": battery,
        # Memory details
        "memory_slots": memory_slots,
        "memory_total_bytes": memory_total_bytes,
    }
