"""
Asset Management Views
Ported from FastAPI app - handles all asset interactions

Key features:
- Auto-creates assets on first visit (get_or_create pattern)
- Hardware scan uploads with lshw parsing
- Intake form updates
- Drive status management
- Audit trail logging (AssetTouch)
"""

import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AssetIntakeForm, DriveStatusForm, HardwareScanUploadForm
from .lshw_parser import extract_serial, format_bytes, parse_disks, parse_lshw_json
from .models import Asset, AssetTouch, Drive, HardwareScan


def _log_touch(asset, touch_type, user, details=None):
    """
    Helper function to log an asset interaction (audit trail).
    Replaces manual INSERT INTO asset_touches from FastAPI.
    """
    AssetTouch.objects.create(
        asset=asset,
        touch_type=touch_type,
        touched_by=user,
        details=details or {},
    )


@login_required
def home(request):
    """
    Home page - shows recent assets
    """
    recent_assets = Asset.objects.select_related("created_by").prefetch_related(
        "hardware_scans"
    )[:20]
    return render(request, "home.html", {"recent_assets": recent_assets})


@login_required
@require_http_methods(["GET", "POST"])
def asset_detail(request, asset_tag):
    """
    Main asset detail view - shows all asset information.

    IMPORTANT: Auto-creates asset on first GET (like FastAPI app)

    Handles:
    - GET: Display asset with all related data
    - POST: Handle intake form OR scan upload
    """
    # Get or create asset (auto-create on first visit!)
    asset, created = Asset.objects.get_or_create(
        asset_tag=asset_tag,
        defaults={"created_by": request.user},
    )

    # REMOVED: View logging causes massive DB bloat from page refreshes
    # Only log meaningful state changes (intake updates, scans, drive status)
    # _log_touch(asset, "view", request.user, {"asset_tag": asset_tag})

    # Get latest hardware scan
    latest_scan = (
        asset.hardware_scans.select_related("scanned_by")
        .order_by("-scanned_at")
        .first()
    )

    # Extract hardware info from latest scan
    cpu_info = None
    hw_summary = None
    # Additional parsed fields we'll expose to the template
    system_info = None
    graphics = []
    network = []
    multimedia = {}
    battery = None
    # Memory defaults to avoid UnboundLocalError when no scan or no parsed memory
    memory_slots = []
    memory_total_bytes = None
    memory_total_human = None
    if latest_scan:
        if latest_scan.summary:
            hw_summary = latest_scan.summary
        if latest_scan.raw_json:
            parsed = parse_lshw_json(latest_scan.raw_json)
            cpu_info = parsed.get("cpu_info")
            # populate additional parsed fields (use sensible defaults)
            system_info = parsed.get("system_info")
            graphics = parsed.get("graphics", []) or []
            network = parsed.get("network", []) or []
            multimedia = parsed.get("multimedia", {}) or {}
            battery = parsed.get("battery")

            # --- Memory parsing: expose per-slot info and a total (bytes & human) ---
            # The parser returns memory_slots (list of dicts) and memory_total_bytes (int)
            memory_slots = parsed.get("memory_slots", []) or []
            memory_total_bytes = parsed.get("memory_total_bytes")
            # Create a human-readable total, e.g. "16.0 GB"
            memory_total_human = None
            if memory_total_bytes:
                try:
                    gb = float(memory_total_bytes) / (1024**3)
                    # show integer GB if whole number, otherwise one decimal
                    if abs(gb - round(gb)) < 0.01:
                        memory_total_human = f"{int(round(gb))} GB"
                    else:
                        memory_total_human = f"{gb:.1f} GB"
                except Exception:
                    memory_total_human = None

            if not hw_summary:
                hw_summary = parsed.get("hw_summary")

    # Get drives
    drives = asset.drives.all()

    # Filter out ephemeral / runtime block devices that come from the live media
    # (examples: mmcblk*, loop*, sr*). We keep the full `drives` queryset for
    # storage but expose `display_drives` to the template for the user-facing list.
    def _is_ephemeral(drive):
        ln = (drive.logicalname or "").lower()
        # Canonicalize common /dev/ names
        if ln.startswith("/dev/"):
            ln = ln[5:]
        # Exclude mmc (mmcblk*), loop devices, and optical (sr*)
        return ln.startswith("mmc") or ln.startswith("loop") or ln.startswith("sr")

    display_drives = [d for d in drives if not _is_ephemeral(d)]

    # Flag that a first-class hard drive is present (used by the UI to show a warning)
    hard_drive_present = bool(display_drives)

    # Get audit trail (touches)
    touches = asset.touches.select_related("touched_by").order_by("-touched_at")[:50]

    # Forms
    intake_form = AssetIntakeForm(instance=asset)
    upload_form = HardwareScanUploadForm()

    context = {
        "asset": asset,
        "latest_scan": latest_scan,
        "cpu_info": cpu_info,
        "hw_summary": hw_summary,
        # New hardware fields exposed to the template
        "system_info": system_info,
        "graphics": graphics,
        "network": network,
        "multimedia": multimedia,
        "battery": battery,
        "drives": drives,
        "display_drives": display_drives,
        "hard_drive_present": hard_drive_present,
        # Memory fields (per-slot and totals) for template display
        "memory_slots": memory_slots,
        "memory_total_bytes": memory_total_bytes,
        "memory_total_human": memory_total_human,
        "touches": touches,
        "intake_form": intake_form,
        "upload_form": upload_form,
        "saved": False,
        "scan_saved": False,
    }

    return render(request, "assets/asset_detail.html", context)


@login_required
@require_http_methods(["POST"])
def asset_intake_update(request, asset_tag):
    """
    Update asset intake information (status, device type, cosmetic grade, etc.)
    Replaces /asset/{asset_tag}/intake_form from FastAPI
    """
    asset = get_object_or_404(Asset, asset_tag=asset_tag)
    form = AssetIntakeForm(request.POST, instance=asset)

    if form.is_valid():
        # Save changes
        updated_asset = form.save()

        # Log the update
        changed_fields = {}
        for field in form.changed_data:
            changed_fields[field] = form.cleaned_data[field]

        _log_touch(
            asset,
            "intake_update",
            request.user,
            {
                "updated_fields": changed_fields,
            },
        )

        messages.success(request, "Asset intake information updated successfully!")
    else:
        messages.error(
            request, "Error updating asset information. Please check the form."
        )

    return redirect("asset_detail", asset_tag=asset_tag)


@login_required
@require_http_methods(["POST"])
def asset_scan_upload(request, asset_tag):
    """
    Upload scan bundle JSON (motherboard.scan_bundle.v1).

    Replaces the old lshw-only upload flow. This view:
    - validates and accepts only the new scan bundle (form enforces schema)
    - requires that bundle.intake.asset_id matches the URL asset_tag
    - computes a canonical sha256 bundle hash and deduplicates
    - stores the raw bundle and bundle metadata on HardwareScan
    - calls the existing lshw parsing logic using bundle['sources']['lshw']
      so existing drive extraction and summary behavior remains unchanged
    - updates/creates Drive records from parsed lshw disks
    - logs the upload via AssetTouch
    """
    import hashlib

    from django.utils.dateparse import parse_datetime

    asset = get_object_or_404(Asset, asset_tag=asset_tag)
    form = HardwareScanUploadForm(request.POST, request.FILES)

    if form.is_valid():
        # Parsed bundle (full scan bundle) is provided by the form
        bundle = form.cleaned_data.get("parsed_json")
        user_notes = form.cleaned_data.get("user_notes", "")

        # Enforce the intake.asset_id matches the URL asset_tag to avoid mis-uploads
        intake = bundle.get("intake", {}) or {}
        bundle_asset_id = str(intake.get("asset_id", "") or "")
        if bundle_asset_id != str(asset_tag):
            messages.error(
                request,
                f"Bundle asset_id '{bundle_asset_id}' does not match this asset '{asset_tag}'. Upload rejected.",
            )
            return redirect("asset_detail", asset_tag=asset_tag)

        # Compute canonical JSON form and sha256 for deduplication
        try:
            canonical = json.dumps(
                bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        except (TypeError, ValueError):
            # Fallback: use normal dumps if some objects aren't serializable in canonical step
            canonical = json.dumps(
                bundle,
                default=str,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        bundle_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        # Dedupe: if identical bundle already ingested for this asset, short-circuit
        existing = HardwareScan.objects.filter(
            asset=asset, bundle_hash=bundle_hash
        ).first()
        if existing:
            messages.success(request, "Duplicate scan bundle (already exists).")
            return redirect("asset_detail", asset_tag=asset_tag)

        # Parse generated_at if present
        gen_at_raw = bundle.get("generated_at")
        generated_at = None
        if gen_at_raw:
            try:
                generated_at = parse_datetime(gen_at_raw)
            except Exception:
                generated_at = None

        # Extract intake duplicate fields for easier queries
        tech_name = intake.get("tech_name", "") or ""
        client_name = intake.get("client_name", "") or ""
        cosmetic_condition = intake.get("cosmetic_condition", "") or ""
        intake_note = intake.get("note", "") or ""

        # Use the lshw source inside the bundle for existing parsing logic
        sources = bundle.get("sources", {}) or {}
        lshw_json = sources.get("lshw")  # expected to be a dict (LSHW JSON)

        # Parse hardware information using existing parser (works on LSHW JSON)
        parsed = {}
        if lshw_json:
            parsed = parse_lshw_json(lshw_json) or {}
        device_serial = parsed.get("device_serial")
        hw_summary = parsed.get("hw_summary")
        disks = parsed.get("disks", []) or []

        # Create HardwareScan record (store full bundle in raw_json and metadata)
        scan = HardwareScan.objects.create(
            asset=asset,
            device_serial=device_serial,
            raw_json=bundle,
            bundle_hash=bundle_hash,
            schema=bundle.get("schema", ""),
            generated_at=generated_at,
            tech_name=tech_name,
            client_name=client_name,
            cosmetic_condition=cosmetic_condition,
            intake_note=intake_note,
            summary=hw_summary,
            scanned_by=request.user,
            user_notes=user_notes,
        )

        # Create/update drive records based on disks extracted from lshw parsing
        created_or_updated = 0
        for disk in disks:
            serial = disk.get("serial")
            # Skip drives with missing/empty serials to prevent duplicates
            if not serial or not serial.strip():
                continue

            defaults = {
                "logicalname": disk.get("logicalname", ""),
                "capacity_bytes": disk.get("size_bytes"),
                "model": disk.get("model", ""),
                "source": "lshw",
            }

            Drive.objects.update_or_create(
                asset=asset,
                serial=serial,
                defaults=defaults,
            )
            created_or_updated += 1

        # Log the upload (audit trail)
        _log_touch(
            asset,
            "scan_upload",
            request.user,
            {
                "scan_id": scan.id,
                "device_serial": device_serial,
                "drive_count": len(disks),
            },
        )

        messages.success(
            request,
            f"Saved scan bundle. Found {len(disks)} drive(s).",
        )
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("asset_detail", asset_tag=asset_tag)


@login_required
@require_http_methods(["POST"])
def drive_status_update(request, asset_tag, drive_id):
    """
    Update drive status (present, removed, wiped, shredded, etc.)
    Replaces /asset/{asset_tag}/drive/{drive_id}/status from FastAPI
    """
    asset = get_object_or_404(Asset, asset_tag=asset_tag)
    drive = get_object_or_404(Drive, id=drive_id, asset=asset)

    form = DriveStatusForm(request.POST, instance=drive)

    if form.is_valid():
        drive = form.save(commit=False)
        drive.status_by = request.user
        drive.save()

        # Log the status change
        _log_touch(
            asset,
            "drive_status",
            request.user,
            {
                "drive_id": drive.id,
                "serial": drive.serial,
                "status": drive.status,
                "status_note": drive.status_note,
            },
        )

        messages.success(
            request, f"Drive status updated to '{drive.get_status_display()}'"
        )
    else:
        messages.error(request, "Error updating drive status.")

    return redirect("asset_detail", asset_tag=asset_tag)


@login_required
def drive_search_by_serial(request):
    """
    Search for drives by serial number.
    Replaces /drive/by_serial from FastAPI

    Returns JSON response with all drives matching the serial.
    """
    serial = request.GET.get("serial", "").strip()

    if not serial:
        return JsonResponse({"error": "Serial number required"}, status=400)

    # Find all drives with this serial
    drives = (
        Drive.objects.filter(serial=serial)
        .select_related("asset", "status_by")
        .order_by("-id")
    )

    matches = []
    for drive in drives:
        matches.append(
            {
                "drive_id": drive.id,
                "asset_tag": drive.asset.asset_tag,
                "drive_serial": drive.serial,
                "logicalname": drive.logicalname,
                "capacity_bytes": drive.capacity_bytes,
                "capacity_human": drive.capacity_human,
                "model": drive.model,
                "status": drive.status,
                "status_note": drive.status_note,
                "status_at": drive.status_at.isoformat() if drive.status_at else None,
            }
        )

    return JsonResponse(
        {
            "serial": serial,
            "count": len(matches),
            "matches": matches,
        }
    )


@login_required
def asset_list_json(request):
    """
    JSON API endpoint - list all assets with basic info
    Useful for external tools or scripts
    """
    assets = Asset.objects.select_related("created_by").order_by("-created_at")[:100]

    data = []
    for asset in assets:
        data.append(
            {
                "asset_tag": asset.asset_tag,
                "status": asset.status,
                "device_type": asset.device_type,
                "location": asset.location,
                "created_at": asset.created_at.isoformat(),
                "created_by": asset.created_by.username,
            }
        )

    return JsonResponse({"assets": data, "count": len(data)})
