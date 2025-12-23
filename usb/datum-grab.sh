#!/usr/bin/env bash
# datums-grab.sh — scan bundle (intake + 7 sources) → <asset_id>.json

set -euo pipefail

# --- User input ---

# Asset ID: validate immediately (URL path segment safe + filename safe)
while :; do
  read -r -p "Asset ID: " asset_id
  asset_id="${asset_id//$'\r'/}"               # strip CR from paste
  asset_id="$(printf '%s' "$asset_id" | xargs)" # trim leading/trailing whitespace

  if [[ -z "$asset_id" ]]; then
    echo "Asset ID required."
    continue
  fi

  if [[ "$asset_id" =~ ^[A-Za-z0-9_-]+$ ]]; then
    break
  fi

  echo "Invalid Asset ID."
  echo "Use only letters/numbers/underscore/dash (A-Z a-z 0-9 _ -). Example: 666 or mb-001"
done

read -r -p "Tech name: " tech_name
read -r -p "Client name: " client_name

while :; do
  read -r -p "Cosmetic condition (A/B/C): " cond
  cond="${cond^^}"
  case "$cond" in
    A|B|C) cosmetic="$cond"; break ;;
    *) echo "Please enter A, B, or C" ;;
  esac
done

read -r -p "Note: " note

outfile="${asset_id}.json"
echo "Scanning $asset_id…"

# Temporary directory (auto-cleaned on exit)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Helper: run command quietly, save stdout/stderr, and capture rc (no set +e/-e needed)
run() {
  local name="$1"; shift
  local bin="$1"

  if command -v "$bin" >/dev/null 2>&1; then
    # Under `set -e`, failures inside an `if` test won't exit the script.
    if "$@" >"$tmp/$name.out" 2>"$tmp/$name.err"; then
      echo 0 >"$tmp/$name.rc"
    else
      echo $? >"$tmp/$name.rc"
    fi
  else
    : >"$tmp/$name.out"
    echo "Command not found: $bin" >"$tmp/$name.err"
    echo 127 >"$tmp/$name.rc"
  fi
}

# Run hardware tools
run lshw   lshw  -json
run lsblk  lsblk -J -b -O
run lspci  lspci -vmm -nn -k
run lsusb  lsusb
run upower upower -d

# --- EDID (connected monitors only) ---
: >"$tmp/edid.out"; : >"$tmp/edid.err"
if command -v edid-decode >/dev/null 2>&1; then
  found=0
  ok=0
  for p in /sys/class/drm/*/edid; do
    [[ -r "$p" ]] || continue
    st="$(dirname "$p")/status"
    [[ -r "$st" ]] || continue
    [[ "$(cat "$st")" == "connected" ]] || continue

    found=1
    printf '===== %s =====\n' "$p" >>"$tmp/edid.out"

    if edid-decode "$p" >>"$tmp/edid.out" 2>>"$tmp/edid.err"; then
      ok=1
    fi
    echo >>"$tmp/edid.out"
  done

  # rc semantics:
  # - 0: tool present and at least one decode succeeded OR nothing connected (not applicable)
  # - 1: tool present, something connected, but no decodes succeeded
  if [[ "$found" -eq 0 ]]; then
    echo 0 >"$tmp/edid.rc"
    : >"$tmp/edid.out"   # keep empty so JSON becomes null
  elif [[ "$ok" -eq 1 ]]; then
    echo 0 >"$tmp/edid.rc"
  else
    echo 1 >"$tmp/edid.rc"
  fi
else
  echo 127 >"$tmp/edid.rc"
  echo "Command not found: edid-decode" >"$tmp/edid.err"
  : >"$tmp/edid.out"
fi

# --- SMART (skip USB drives) ---
: >"$tmp/smart.out"; : >"$tmp/smart.err"
if command -v smartctl >/dev/null 2>&1; then
  found=0
  ran=0

  while read -r dev tran; do
    [[ -n "${dev:-}" ]] || continue
    [[ "${tran:-}" == "usb" ]] && continue

    found=1
    printf '===== /dev/%s =====\n' "$dev" >>"$tmp/smart.out"

    # smartctl rc can be nonzero for "disk failing" (still valuable data),
    # so we treat "ran at least once" as success for the collector.
    if smartctl -i -H -A "/dev/$dev" >>"$tmp/smart.out" 2>>"$tmp/smart.err"; then
      ran=1
    else
      ran=1
    fi
    echo >>"$tmp/smart.out"
  done < <(lsblk -dno NAME,TRAN 2>/dev/null || true)

  # rc semantics:
  # - 0: tool present and we ran smartctl at least once OR no internal disks found (not applicable)
  # - 1: internal disks found but smartctl couldn't be run at all (rare; still captured in stderr)
  if [[ "$found" -eq 0 ]]; then
    echo 0 >"$tmp/smart.rc"
    : >"$tmp/smart.out"  # keep empty so JSON becomes null
  elif [[ "$ran" -eq 1 ]]; then
    echo 0 >"$tmp/smart.rc"
  else
    echo 1 >"$tmp/smart.rc"
  fi
else
  echo 127 >"$tmp/smart.rc"
  echo "Command not found: smartctl" >"$tmp/smart.err"
  : >"$tmp/smart.out"
fi

# --- Show scan status ---
echo
echo "=== Scan status ==="
for tool in lshw lsblk lspci lsusb upower edid smart; do
  rc="$(cat "$tmp/$tool.rc" 2>/dev/null || echo 1)"
  if [[ "$rc" -eq 0 ]]; then
    printf "  %-7s OK\n" "$tool"
  elif [[ "$rc" -eq 127 ]]; then
    printf "  %-7s MISSING\n" "$tool"
  else
    printf "  %-7s rc=%s\n" "$tool" "$rc"
  fi
done
echo

# --- Build JSON (sources + meta.status) ---
jq -n \
  --arg schema "motherboard.scan_bundle.v1" \
  --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg hostname "$(hostname)" \
  --arg user "${SUDO_USER:-$USER}" \
  --arg asset_id "$asset_id" \
  --arg tech_name "$tech_name" \
  --arg client_name "$client_name" \
  --arg cosmetic "$cosmetic" \
  --arg note "$note" \
  --slurpfile sources <(
    jq -n \
      --rawfile lshw   "$tmp/lshw.out" \
      --rawfile lsblk  "$tmp/lsblk.out" \
      --rawfile lspci  "$tmp/lspci.out" \
      --rawfile lsusb  "$tmp/lsusb.out" \
      --rawfile upower "$tmp/upower.out" \
      --rawfile edid   "$tmp/edid.out" \
      --rawfile smart  "$tmp/smart.out" \
      '
      def nullifempty(s): if (s|length)==0 then null else s end;
      {
        lshw:   ($lshw  | fromjson? // null),
        lsblk:  ($lsblk | fromjson? // null),
        lspci:  nullifempty($lspci),
        lsusb:  nullifempty($lsusb),
        upower: nullifempty($upower),
        edid:   nullifempty($edid),
        smart:  nullifempty($smart)
      }'
  ) \
  --slurpfile meta <(
    jq -n \
      --rawfile lshw_err   "$tmp/lshw.err"   --arg lshw_rc   "$(cat "$tmp/lshw.rc")" \
      --rawfile lsblk_err  "$tmp/lsblk.err"  --arg lsblk_rc  "$(cat "$tmp/lsblk.rc")" \
      --rawfile lspci_err  "$tmp/lspci.err"  --arg lspci_rc  "$(cat "$tmp/lspci.rc")" \
      --rawfile lsusb_err  "$tmp/lsusb.err"  --arg lsusb_rc  "$(cat "$tmp/lsusb.rc")" \
      --rawfile upower_err "$tmp/upower.err" --arg upower_rc "$(cat "$tmp/upower.rc")" \
      --rawfile edid_err   "$tmp/edid.err"   --arg edid_rc   "$(cat "$tmp/edid.rc")" \
      --rawfile smart_err  "$tmp/smart.err"  --arg smart_rc  "$(cat "$tmp/smart.rc")" \
      '
      def nullifempty(s): if (s|length)==0 then null else s end;
      def num(s): (s|tonumber);
      {
        lshw:   { rc: num($lshw_rc),   stderr: nullifempty($lshw_err)   },
        lsblk:  { rc: num($lsblk_rc),  stderr: nullifempty($lsblk_err)  },
        lspci:  { rc: num($lspci_rc),  stderr: nullifempty($lspci_err)  },
        lsusb:  { rc: num($lsusb_rc),  stderr: nullifempty($lsusb_err)  },
        upower: { rc: num($upower_rc), stderr: nullifempty($upower_err) },
        edid:   { rc: num($edid_rc),   stderr: nullifempty($edid_err)   },
        smart:  { rc: num($smart_rc),  stderr: nullifempty($smart_err)  }
      }'
  ) \
  '{
    schema: $schema,
    generated_at: $generated_at,
    scanner: { hostname: $hostname, user: $user },
    intake: {
      asset_id: $asset_id,
      tech_name: $tech_name,
      client_name: $client_name,
      cosmetic_condition: $cosmetic,
      note: $note
    },
    sources: $sources[0],
    meta: { status: $meta[0] }
  }' >"$tmp/bundle.json"

# --- Confirm save ---
echo "Intake summary:"
echo "  Asset: $asset_id | Tech: $tech_name | Client: $client_name"
echo "  Condition: $cosmetic | Note: $note"
echo
read -r -p "Write $outfile? (y/N): " confirm
if [[ "${confirm,,}" == y* ]]; then
  mv "$tmp/bundle.json" "$outfile"
  echo "Saved → $outfile"
  echo
  echo "Next steps:"
  echo "  1) You may now attach the Asset ID sticker to the device."
  echo "  2) You can remove the USB drive."
  echo "  3) Ensure data security: follow chain-of-custody and keep the device in a secure area."
  echo
else
  echo "Cancelled — nothing saved."
  echo
fi
