# CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-12-17

### Fixed - Critical Bug Fixes (AI-Identified)

#### 🐛 Bug #1: Drive.capacity_human Mutation (CRITICAL)
**Problem:** The `capacity_human` property in `assets/models.py` was mutating `self.capacity_bytes` by dividing it in-place during formatting. This could corrupt data if the model instance was saved after accessing this property.

**Fix:** Changed to use a local variable `bytes_remaining` instead of modifying the model field.

**Impact:** Prevents potential data corruption in drive capacity tracking.

**Files Changed:**
- `assets/models.py` (Drive model, lines 147-158)

---

#### 🐛 Bug #2: Audit Trail Spam from Page Views
**Problem:** Every GET request to `asset_detail` was logging a "view" touch record, causing massive database bloat from normal navigation and page refreshes.

**Fix:** Removed automatic view logging. Audit trail now only logs meaningful state changes:
- Hardware scan uploads
- Intake form updates
- Drive status changes

**Impact:** Dramatically reduces database growth and improves performance.

**Files Changed:**
- `assets/views.py` (asset_detail view, lines 69-71)

---

#### 🐛 Bug #3: Missing Drive Serial Handling
**Problem:** Drive creation with `update_or_create` used `serial=disk.get("serial")` without validation. If serial was None or empty, could create duplicate drives or break serial searches.

**Fix:** Added validation to skip drives with missing/empty serials before attempting to create Drive records.

**Impact:** Prevents duplicate drive records and database integrity issues.

**Files Changed:**
- `assets/views.py` (asset_scan_upload view, lines 195-200)

---

### Added - Production Improvements

#### ⚙️ Production Docker Profile
**Added:** New production-ready Docker Compose configuration:
- Uses Gunicorn instead of Django development server
- Sets `DEBUG=False` automatically
- Runs `collectstatic` on startup
- 4 workers with 120s timeout
- Database port not exposed to host in production
- pgAdmin disabled in production profile

**Usage:**
```bash
# Development (default)
docker-compose up

# Production
docker-compose --profile production up web-prod db
```

**Files Changed:**
- `docker-compose.yml`
- `requirements.txt` (added gunicorn)

---

#### 📄 License Added
**Added:** Proprietary license file to clarify usage rights and contribution terms.

**Key Points:**
- Source code viewable for educational purposes
- Commercial use requires licensing from Motherboard, Inc.
- Only authorized contributors (employees/contractors) may modify
- All contributions become property of Motherboard, Inc.

**Files Added:**
- `LICENSE`

---

### Security Improvements

#### 🔒 Default Credentials Warning
**Enhanced:** Added prominent warnings in documentation about changing default credentials:
- `admin/admin123` must be changed in production
- Updated README.md with security checklist
- Added production deployment guidelines

---

## [1.0.0] - 2025-12-17 - Initial Release

### Added
- Complete Django-based asset tracking system
- Hardware scan upload with lshw parser
- Drive lifecycle management (present, wiped, shredded, removed)
- Auto-creation of assets on first visit
- Complete audit trail system
- Django Admin interface
- RESTful JSON API endpoints
- Docker Compose deployment
- PostgreSQL database
- pgAdmin4 interface
- Comprehensive documentation (README, QUICKSTART, deployment guides)

### Migrated
- Ported from FastAPI to Django
- Replaced raw SQL with Django ORM
- Replaced HTTP Basic Auth with Django authentication
- Added form validation
- Added database migrations

---

## Credits

**Bug Identification:** Grok AI & ChatGPT (December 17, 2025)
**Original Assessment:** 8.5/10 → Expected 9+/10 with fixes applied

**Review Highlights:**
- "Very solid, thoughtfully designed"
- "Impressively high quality for a new project"
- "Excellent documentation (rare for small repos)"
- "Production-aware and easy to deploy"

**Key Strengths Noted:**
- Niche focus on IT asset refurbishing/e-waste management
- Drive lifecycle compliance tracking
- Outstanding deployability with Docker
- Clean Django architecture

---

## Development Team

**Copyright:** Motherboard, Inc. (2025)
**Primary Developer:** Stephen (stephen@motherboardrecycling.org)
**AI Assistant:** Claude (Anthropic)

---

## Next Steps (Recommended)

### High Priority
- [ ] Add basic unit tests (models, views, forms)
- [ ] Add integration tests for hardware scan upload flow
- [ ] Test production Docker profile thoroughly
- [ ] Deploy to staging environment

### Medium Priority
- [ ] Extract business logic into service layer
- [ ] Add rate limiting for API endpoints
- [ ] Enhance serial number normalization (trim, uppercase)
- [ ] Add database indexes for common queries

### Low Priority
- [ ] Add data export functionality (CSV, Excel)
- [ ] Create reporting dashboard
- [ ] Add email notifications for key events
- [ ] Integrate with barcode scanning hardware

---

## Version History

- **v1.0.0** (2025-12-17) - Initial Django release, migrated from FastAPI
- **v0.x** (2024-2025) - FastAPI prototype (private repository)