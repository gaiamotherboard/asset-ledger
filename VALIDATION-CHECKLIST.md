# Validation Checklist for Asset Management System

This document provides a comprehensive testing plan to validate all features of the asset management system, with special focus on memory slot rendering, ephemeral drive filtering, and data integrity.

## Prerequisites

Before starting validation:

- [ ] Docker Compose dev stack is running: `docker compose --profile dev up -d --build`
- [ ] Database migrations are applied: `docker compose exec web python manage.py migrate`
- [ ] Test user account created: `docker compose exec web python manage.py createsuperuser`
- [ ] Sample LSHW JSON files prepared (see examples below)

## 1. Memory Slot Rendering Tests

### Test 1.1: Single Memory Slot Display

**Objective:** Verify that a system with one memory slot displays correctly.

**Steps:**
1. Create a new asset (visit `/asset/MEM-TEST-001/`)
2. Upload LSHW JSON with single 8GB memory slot (see `lshw-single-8gb.json` below)
3. Verify asset detail page shows:
   - [ ] Total memory: "8 GB" (or "8.0 GB")
   - [ ] Memory slots section with 1 slot
   - [ ] Slot name (e.g., "DIMM 0" or "DIMM A")
   - [ ] Size: "8.0 GB"
   - [ ] Vendor name displayed
   - [ ] Product/Part number displayed
   - [ ] Serial number displayed (if present)

**Expected Result:** Memory information renders without errors, displays human-readable sizes.

---

### Test 1.2: Dual Memory Slot Display

**Objective:** Verify that a system with two memory slots displays correctly and totals sum properly.

**Steps:**
1. Create a new asset (visit `/asset/MEM-TEST-002/`)
2. Upload LSHW JSON with two 8GB memory slots (see `lshw-dual-8gb.json` below)
3. Verify asset detail page shows:
   - [ ] Total memory: "16 GB" (or "16.0 GB")
   - [ ] Memory slots section with 2 slots
   - [ ] Each slot shows correct size (8.0 GB each)
   - [ ] Each slot shows vendor and product info
   - [ ] Slots are clearly separated/distinguishable

**Expected Result:** Total memory is correct (16 GB), both slots render properly.

---

### Test 1.3: No Memory Information

**Objective:** Verify graceful handling when LSHW has no memory data.

**Steps:**
1. Create a new asset (visit `/asset/MEM-TEST-003/`)
2. Upload minimal LSHW JSON with no memory nodes
3. Verify asset detail page shows:
   - [ ] Total memory: "Unknown" (not blank or error)
   - [ ] Message: "No per-slot memory information available."
   - [ ] No template errors or crashes

**Expected Result:** Page renders cleanly with appropriate "no data" messaging.

---

### Test 1.4: Mixed Memory Sizes

**Objective:** Verify handling of non-uniform memory configurations.

**Steps:**
1. Create a new asset (visit `/asset/MEM-TEST-004/`)
2. Upload LSHW JSON with 4GB + 8GB memory slots (12GB total)
3. Verify asset detail page shows:
   - [ ] Total memory: "12 GB" (or "12.0 GB")
   - [ ] First slot: "4.0 GB"
   - [ ] Second slot: "8.0 GB"
   - [ ] Both slots display correctly

**Expected Result:** Different-sized slots display correctly, total is accurate.

---

## 2. Ephemeral Drive Filtering Tests

### Test 2.1: Boot Media Exclusion (mmcblk)

**Objective:** Verify that USB/SD boot media (mmcblk devices) are filtered from display.

**Steps:**
1. Create a new asset (visit `/asset/DRIVE-TEST-001/`)
2. Upload LSHW JSON with `/dev/mmcblk0` device (32GB USB boot stick)
3. Verify asset detail page shows:
   - [ ] Drive count: 0 (or "(Boot media excluded)" note visible)
   - [ ] mmcblk drive is NOT displayed in drive list
   - [ ] NO hard drive warning banner
   - [ ] "No drives detected" message OR empty drive list

**Expected Result:** Boot media is hidden from user view.

---

### Test 2.2: Loop Device Exclusion

**Objective:** Verify that loop devices (squashfs, live media) are filtered.

**Steps:**
1. Create a new asset (visit `/asset/DRIVE-TEST-002/`)
2. Upload LSHW JSON with `/dev/loop0` and `/dev/loop1` devices
3. Verify asset detail page shows:
   - [ ] Loop devices are NOT displayed
   - [ ] Drive count is 0
   - [ ] No hard drive warning

**Expected Result:** Loop devices are invisible to user.

---

### Test 2.3: Optical Drive Exclusion (sr0)

**Objective:** Verify that optical drives (sr*, CD/DVD) are filtered.

**Steps:**
1. Create a new asset (visit `/asset/DRIVE-TEST-003/`)
2. Upload LSHW JSON with `/dev/sr0` device (CD-ROM drive)
3. Verify asset detail page shows:
   - [ ] sr0 is NOT displayed
   - [ ] Drive count is 0
   - [ ] No hard drive warning

**Expected Result:** Optical drives are hidden.

---

### Test 2.4: Real Hard Drive Detection

**Objective:** Verify that legitimate hard drives (sda, nvme) ARE displayed and trigger warning.

**Steps:**
1. Create a new asset (visit `/asset/DRIVE-TEST-004/`)
2. Upload LSHW JSON with `/dev/sda` 256GB Samsung SSD
3. Verify asset detail page shows:
   - [ ] Drive count: 1
   - [ ] Drive is displayed with model, capacity, serial
   - [ ] **WARNING BANNER**: "First-class hard drive detected..."
   - [ ] Quick action buttons: "Hard drive removed", "Hard drive wipe"

**Expected Result:** Real drive shows, warning banner appears, quick actions available.

---

### Test 2.5: Mixed Drive Scenario

**Objective:** Verify filtering works when boot media AND real drives are both present.

**Steps:**
1. Create a new asset (visit `/asset/DRIVE-TEST-005/`)
2. Upload LSHW JSON with:
   - `/dev/mmcblk0` (32GB USB boot)
   - `/dev/sda` (500GB HDD)
3. Verify asset detail page shows:
   - [ ] Drive count: 1 (only sda counted)
   - [ ] mmcblk0 is NOT displayed
   - [ ] sda IS displayed
   - [ ] Warning banner appears (for sda)

**Expected Result:** Only real drive shows; ephemeral media hidden.

---

## 3. Drive Status Quick Actions

### Test 3.1: "Hard drive removed" Quick Action

**Objective:** Verify quick action updates drive status and logs to audit trail.

**Steps:**
1. On asset with real drive, click "Hard drive removed" button
2. Verify:
   - [ ] Page reloads/redirects to asset detail
   - [ ] Success message: "Drive status updated to 'Removed'"
   - [ ] Drive status now shows: "Removed"
   - [ ] Activity log has new entry: "Drive Status Changed"
   - [ ] Activity entry shows user and timestamp
   - [ ] No template errors

**Expected Result:** Drive status updates, audit trail logs action.

---

### Test 3.2: "Hard drive wipe" Quick Action

**Objective:** Verify wipe action updates status correctly.

**Steps:**
1. On asset with real drive, click "Hard drive wipe" button
2. Verify:
   - [ ] Success message appears
   - [ ] Drive status: "Wiped"
   - [ ] Activity log entry: "Drive Status Changed"
   - [ ] Details show wiped status

**Expected Result:** Drive marked as wiped, logged to audit trail.

---

## 4. Data Integrity Tests

### Test 4.1: Duplicate Drive Serial Handling

**Objective:** Verify that uploading same drive twice doesn't create duplicates.

**Steps:**
1. Create asset and upload LSHW with drive serial "ABC123"
2. Upload same LSHW file again
3. Verify:
   - [ ] Drive count remains 1 (not 2)
   - [ ] No duplicate drive entries
   - [ ] Multiple hardware scans recorded
   - [ ] Latest scan shows in UI

**Expected Result:** Drive records use update_or_create, no duplicates.

---

### Test 4.2: Empty/Missing Serial Handling

**Objective:** Verify that drives without serials are handled gracefully.

**Steps:**
1. Upload LSHW JSON with drive that has no serial field or empty serial
2. Verify:
   - [ ] No database error or crash
   - [ ] Drive may be skipped (preferred) OR
   - [ ] Drive created with synthetic serial (e.g., "NOSERIAL-{hash}")
   - [ ] No duplicate null serial entries

**Expected Result:** System doesn't crash, handles missing serials safely.

---

### Test 4.3: Null Field Prevention

**Objective:** Verify that all model fields have safe defaults (no NULL violations).

**Steps:**
1. Create asset with minimal data
2. Upload LSHW with incomplete data
3. Check database:
   ```bash
   docker compose exec db psql -U postgres -d assetdb -c "SELECT * FROM assets_drive WHERE model IS NULL;"
   ```
4. Verify:
   - [ ] No NULL values in non-nullable text fields
   - [ ] Empty strings used as defaults where appropriate

**Expected Result:** No NULL constraint violations.

---

## 5. Audit Trail (AssetTouch) Tests

### Test 5.1: Scan Upload Logging

**Objective:** Verify scan uploads are logged.

**Steps:**
1. Upload hardware scan
2. Check activity log on asset detail page
3. Verify:
   - [ ] Entry: "Hardware Scan Uploaded"
   - [ ] Shows username and timestamp
   - [ ] Details include scan ID and drive count

**Expected Result:** Scan upload creates audit trail entry.

---

### Test 5.2: Drive Status Change Logging

**Objective:** Verify drive status changes are logged with details.

**Steps:**
1. Update drive status using full form (not quick action)
2. Add note: "Test note for audit"
3. Verify activity log shows:
   - [ ] Entry: "Drive Status Changed"
   - [ ] Drive serial in details
   - [ ] New status in details
   - [ ] Note text preserved

**Expected Result:** All status changes logged with full context.

---

### Test 5.3: Intake Update Logging

**Objective:** Verify intake form updates are logged.

**Steps:**
1. Update asset status to "Testing"
2. Set device type to "Laptop"
3. Save intake form
4. Verify activity log shows:
   - [ ] Entry: "Intake Information Updated"
   - [ ] Changed fields listed in details

**Expected Result:** Form changes tracked in audit trail.

---

## 6. Production Readiness Tests

### Test 6.1: Migration Safety

**Objective:** Verify migrations run cleanly on fresh database.

**Steps:**
1. Stop containers: `docker compose down -v` (removes DB!)
2. Recreate: `docker compose --profile dev up -d --build`
3. Verify:
   - [ ] Web container starts successfully
   - [ ] No migration errors in logs: `docker compose logs web`
   - [ ] Database schema created
   - [ ] Can create superuser
   - [ ] Can access admin: http://localhost:8001/admin/

**Expected Result:** Clean migrations, no errors.

---

### Test 6.2: Unit Test Suite

**Objective:** Run automated tests to verify core functionality.

**Steps:**
1. Run tests:
   ```bash
   docker compose exec web python manage.py test assets
   ```
2. Verify:
   - [ ] All tests pass (0 failures, 0 errors)
   - [ ] Memory slot parsing tests pass
   - [ ] Format bytes tests pass
   - [ ] Drive model tests pass
   - [ ] Asset creation tests pass

**Expected Result:** Full test suite passes.

---

### Test 6.3: Static Files Collection

**Objective:** Verify static files work for production deployment.

**Steps:**
1. Run collectstatic:
   ```bash
   docker compose exec web python manage.py collectstatic --noinput
   ```
2. Verify:
   - [ ] Static files collected to `/app/staticfiles/`
   - [ ] No errors or warnings
   - [ ] Admin CSS/JS accessible

**Expected Result:** Static files ready for nginx/production.

---

## 7. Sample LSHW JSON Files

### lshw-single-8gb.json
```json
{
  "id": "computer",
  "class": "system",
  "description": "Computer",
  "product": "Test Laptop",
  "vendor": "TestVendor",
  "serial": "TESTSERIAL123",
  "children": [
    {
      "id": "core",
      "class": "bus",
      "children": [
        {
          "id": "cpu",
          "class": "processor",
          "product": "Intel Core i5-8250U",
          "vendor": "Intel Corp."
        },
        {
          "id": "memory",
          "class": "memory",
          "description": "System Memory",
          "size": 8589934592,
          "children": [
            {
              "id": "bank:0",
              "class": "memory",
              "description": "SODIMM DDR4",
              "slot": "DIMM 0",
              "size": 8589934592,
              "vendor": "Samsung",
              "product": "M471A1K43CB1-CTD",
              "serial": "MEMSERIAL001"
            }
          ]
        }
      ]
    }
  ]
}
```

### lshw-dual-8gb.json
```json
{
  "id": "computer",
  "class": "system",
  "children": [
    {
      "id": "core",
      "class": "bus",
      "children": [
        {
          "id": "cpu",
          "class": "processor",
          "product": "Intel Core i7-10700"
        },
        {
          "id": "memory",
          "class": "memory",
          "description": "System Memory",
          "size": 17179869184,
          "children": [
            {
              "id": "bank:0",
              "class": "memory",
              "slot": "DIMM A",
              "size": 8589934592,
              "vendor": "Crucial",
              "product": "CT8G4SFRA266.C8FE",
              "serial": "MEM001"
            },
            {
              "id": "bank:1",
              "class": "memory",
              "slot": "DIMM B",
              "size": 8589934592,
              "vendor": "Crucial",
              "product": "CT8G4SFRA266.C8FE",
              "serial": "MEM002"
            }
          ]
        }
      ]
    }
  ]
}
```

### lshw-boot-media-only.json
```json
{
  "id": "computer",
  "class": "system",
  "children": [
    {
      "id": "core",
      "class": "bus",
      "children": [
        {
          "id": "storage",
          "class": "storage",
          "children": [
            {
              "id": "disk",
              "class": "disk",
              "logicalname": "/dev/mmcblk0",
              "size": 32212254720,
              "product": "USB SD Reader",
              "serial": "USB123456"
            }
          ]
        }
      ]
    }
  ]
}
```

### lshw-real-drive.json
```json
{
  "id": "computer",
  "class": "system",
  "serial": "LAPTOP001",
  "children": [
    {
      "id": "core",
      "class": "bus",
      "children": [
        {
          "id": "cpu",
          "class": "processor",
          "product": "Intel Core i5-7200U"
        },
        {
          "id": "memory",
          "class": "memory",
          "description": "System Memory",
          "size": 8589934592
        },
        {
          "id": "storage",
          "class": "storage",
          "children": [
            {
              "id": "disk",
              "class": "disk",
              "logicalname": "/dev/sda",
              "size": 256060514304,
              "product": "Samsung SSD 850",
              "vendor": "Samsung",
              "serial": "S2RBNX0J123456Z"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 8. Sign-Off Checklist

Before considering the system production-ready:

- [ ] All memory slot tests (1.1-1.4) passed
- [ ] All ephemeral drive filtering tests (2.1-2.5) passed
- [ ] All quick action tests (3.1-3.2) passed
- [ ] All data integrity tests (4.1-4.3) passed
- [ ] All audit trail tests (5.1-5.3) passed
- [ ] All production readiness tests (6.1-6.3) passed
- [ ] Unit test suite passes completely
- [ ] Documentation is up to date
- [ ] Known issues documented (if any)
- [ ] Backup/restore procedure tested
- [ ] Performance acceptable with 100+ assets

---

## 9. Known Limitations

Document any known issues or limitations here:

1. **Ephemeral drive filter**: Currently uses logical name heuristics (mmc*, loop*, sr*). If your boot media appears as /dev/sdX, you may need to add vendor/model filtering.

2. **Memory total fallback**: If LSHW doesn't provide a system memory node and slots don't have sizes, memory total will be derived from hw_summary.ram string parsing (best effort).

3. **View logging disabled**: Asset views no longer create audit entries to prevent DB bloat. Only meaningful actions (scans, status changes) are logged.

---

## 10. Next Steps After Validation

Once all tests pass:

1. **Production hardening**:
   - Remove pgAdmin from production compose
   - Set `DEBUG=False` in settings
   - Use proper SECRET_KEY (not hardcoded)
   - Set up proper ALLOWED_HOSTS
   - Configure nginx for static files
   - Set up SSL/TLS certificates

2. **Operational concerns**:
   - Set up database backups
   - Configure log rotation
   - Set up monitoring/alerting
   - Document backup/restore procedures
   - Create admin runbook

3. **Optional enhancements**:
   - Bulk import from spreadsheet
   - Export to CSV
   - Advanced search/filtering
   - Drive serial search improvements
   - Cosmetic grading photos
   - Labels/tags for assets

---

**Last Updated:** 2024-01-XX  
**Version:** 1.0  
**Maintainer:** [Your Name/Team]