# Asset Control Panel - Django Edition

A comprehensive asset tracking and inventory management system built with Django. This application tracks IT hardware assets through intake, testing, and disposal, with special emphasis on drive lifecycle tracking and compliance documentation.

## 🎯 What This Application Does

- **Asset Tracking**: Manage IT assets (laptops, desktops, servers) with unique asset tags
- **Hardware Scanning**: Upload comprehensive scan bundle JSON files that capture detailed hardware information from multiple sources (lshw, lsblk, lspci, lsusb, SMART data, etc.)
- **Drive Management**: Track individual storage drives through their lifecycle (present, wiped, shredded, removed)
- **Audit Trail**: Complete history of every interaction with every asset
- **Auto-Creation**: Assets are automatically created on first visit - no pre-registration needed
- **Deduplication**: Scan bundles are deduplicated using SHA-256 hashing to prevent duplicate uploads
- **Per-Source Status Tracking**: View return codes and error output for each hardware detection tool
- **Web Interface**: User-friendly forms and dashboards
- **Admin Panel**: Django's powerful admin interface for advanced management
- **JSON API**: RESTful endpoints for programmatic access

## 🏗️ Architecture

**Technology Stack:**
- **Django 5.0**: Python web framework
- **PostgreSQL 16**: Database
- **Docker Compose**: Container orchestration
- **pgAdmin4**: Database management interface
- **Tailwind CSS**: Frontend styling
- **daisyUI (Tailwind plugin / CDN-ready)**: Lightweight component library and theme set used to prettify the UI and provide multiple color themes without changing backend logic.

Note: A theme switcher was added to the main user-facing templates (e.g. `templates/login.html` and `templates/home.html`). The switcher toggles daisyUI themes by setting `data-theme` on the document root and persists the selection in browser `localStorage`. No backend code or endpoints were changed — the theme handling is purely client-side. To customize available themes or integrate daisyUI into your Tailwind build, update the templates or your Tailwind config/build pipeline accordingly.

**Docker Services:**
- `web` - Django application (port 8000)
- `db` - PostgreSQL database (port 5432)
- `pgadmin` - Database admin tool (port 5050)

## 📋 Prerequisites

- Docker and Docker Compose installed
- Basic familiarity with terminal/command line
- That's it! Everything else runs in containers.

## 🚀 Quick Start Guide

### Step 1: Configure Environment Variables

1. Copy the `.env` file and customize if needed (the defaults work for testing):

```bash
# The .env file is already created with default values
# For production, you MUST change the passwords!
```

**Important Environment Variables:**
- `POSTGRES_PASSWORD`: Database password
- `DJANGO_SECRET_KEY`: Django secret (change in production!)
- `DJANGO_SUPERUSER_USERNAME`: Admin username (default: admin)
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (default: admin123)

### Step 2: Build and Start the Application

```bash
# Navigate to the control-panel directory
cd ~/Desktop/control-panel

# Build and start all containers
docker-compose up --build
```

**What happens during startup:**
1. Docker builds the Django container
2. PostgreSQL database starts and initializes
3. Django runs database migrations (creates tables)
4. Django auto-creates the admin user
5. Django development server starts on port 8000

**You'll see output like:**
```
✓ Superuser 'admin' created successfully!
  Login at http://localhost:8000/admin/ or http://localhost:8000/login/
  Username: admin
  Password: admin123
```

### Step 3: Access the Application

Open your browser and visit:

- **Main App**: http://localhost:8000/
- **Login Page**: http://localhost:8000/login/
- **Django Admin**: http://localhost:8000/admin/
- **pgAdmin**: http://localhost:5050/

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 📖 How to Use

### Creating Your First Asset

Assets are **auto-created** on first visit (just like the FastAPI version):

1. Log in to http://localhost:8000/login/
2. On the home page, enter an asset tag (e.g., `LAPTOP-001`)
3. Click "Go to Asset"
4. The asset is automatically created!

### Uploading Hardware Information

The system accepts **Scan Bundle JSON** files conforming to the `motherboard.scan_bundle.v1` schema. These bundles contain comprehensive hardware information from multiple sources.

**Quick Upload:**
1. Navigate to an asset detail page (e.g., `/asset/666/`)
2. Find the "Upload Scan Bundle JSON" section
3. Choose your scan bundle JSON file
4. Add optional notes
5. Click "Upload"

**What Happens During Upload:**
- The system validates the JSON schema and structure
- Computes a SHA-256 hash of the bundle for deduplication
- If the exact same bundle was already uploaded, it's skipped (no duplicate storage)
- Extracts hardware information from the `sources.lshw` section
- Creates/updates Drive records for detected storage devices
- Stores the complete bundle with all metadata
- Displays per-source status (return codes, stderr) in the UI
- Logs the upload in the audit trail

### Understanding Scan Bundles

A **Scan Bundle** is a comprehensive JSON document that captures hardware information from multiple diagnostic tools. Unlike simple LSHW-only uploads, scan bundles provide:

- **Multiple Data Sources**: lshw, lsblk, lspci, lsusb, upower, edid, smartctl
- **Per-Source Status**: Return code and stderr for each tool (helps diagnose scanning issues)
- **Scanner Metadata**: Hostname and username of the scanning machine
- **Intake Metadata**: Tech name, client info, cosmetic condition, notes
- **Timestamp**: When the scan was generated
- **Deduplication**: SHA-256 hash prevents duplicate uploads

## 📋 Scan Bundle JSON Format

### Schema: `motherboard.scan_bundle.v1`

The scan bundle follows a strict schema. Here's the complete structure:

```json
{
  "schema": "motherboard.scan_bundle.v1",
  "generated_at": "2024-12-22T10:30:45.123456Z",
  "scanner": {
    "hostname": "live-usb-workstation",
    "user": "techuser"
  },
  "intake": {
    "asset_id": "666",
    "tech_name": "John Smith",
    "client_name": "Acme Corp",
    "cosmetic_condition": "B",
    "note": "Minor scratches on lid, otherwise good condition"
  },
  "sources": {
    "lshw": { /* full lshw JSON output */ },
    "lsblk": { /* lsblk JSON output */ },
    "lspci": "00:00.0 Host bridge: Intel Corporation...\n00:02.0 VGA...",
    "lsusb": "Bus 001 Device 001: ID 1d6b:0002 Linux Foundation...",
    "upower": "Device: /org/freedesktop/UPower/devices/battery_BAT0...",
    "edid": "00ffffffffffff004d10...",
    "smart": {
      "/dev/sda": "=== START OF INFORMATION SECTION ===\nModel Family: Samsung..."
    }
  },
  "meta": {
    "status": {
      "lshw": {
        "rc": 0,
        "stderr": ""
      },
      "lsblk": {
        "rc": 0,
        "stderr": ""
      },
      "lspci": {
        "rc": 0,
        "stderr": ""
      },
      "lsusb": {
        "rc": 0,
        "stderr": ""
      },
      "upower": {
        "rc": 0,
        "stderr": "WARNING: No battery detected"
      },
      "edid": {
        "rc": 0,
        "stderr": ""
      },
      "smart": {
        "rc": 0,
        "stderr": ""
      }
    }
  }
}
```

### Field Descriptions

#### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema` | string | ✅ Yes | Must be `"motherboard.scan_bundle.v1"` |
| `generated_at` | string (ISO 8601) | ✅ Yes | UTC timestamp when the scan was performed |
| `scanner` | object | ✅ Yes | Information about the scanning system |
| `intake` | object | ✅ Yes | Asset intake metadata |
| `sources` | object | ✅ Yes | Hardware data from various tools |
| `meta` | object | ✅ Yes | Metadata about the scan process |

#### Scanner Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hostname` | string | ✅ Yes | Hostname of the machine performing the scan |
| `user` | string | ✅ Yes | Username running the scanner |

#### Intake Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asset_id` | string | ✅ Yes | Must match the asset tag in the URL |
| `tech_name` | string | ❌ No | Name of technician performing intake |
| `client_name` | string | ❌ No | Client or source of the asset |
| `cosmetic_condition` | string | ❌ No | Grade: A, B, C, or D |
| `note` | string | ❌ No | Free-form notes about condition |

#### Sources Object

Contains the actual hardware data. The system **requires** at least `lshw` to be present, as it's used for drive extraction and hardware parsing.

| Source | Type | Required | Description |
|--------|------|----------|-------------|
| `lshw` | object (JSON) | ✅ Yes | Full lshw JSON output (`sudo lshw -json`) |
| `lsblk` | object (JSON) | ❌ No | Block device info (`lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT`) |
| `lspci` | string (text) | ❌ No | PCI device list (`lspci -vv`) |
| `lsusb` | string (text) | ❌ No | USB device list (`lsusb -v`) |
| `upower` | string (text) | ❌ No | Battery/power info (`upower -d`) |
| `edid` | string (hex) | ❌ No | Display EDID data |
| `smart` | object | ❌ No | SMART data per drive, keyed by device path |

#### Meta Object

Contains execution status for each data source.

```json
{
  "status": {
    "<source_name>": {
      "rc": 0,           // Return code (0 = success)
      "stderr": ""       // Standard error output
    }
  }
}
```

**Status Interpretation:**
- `rc: 0` - Command succeeded
- `rc: 1` or higher - Command failed (check stderr for details)
- `stderr: ""` - No errors
- `stderr: "text"` - Warning or error messages

### Creating a Scan Bundle

You need to create a script or tool that:

1. **Runs hardware detection commands**
2. **Collects output from each tool**
3. **Captures return codes and stderr**
4. **Assembles the JSON bundle**
5. **Saves to a file**

**Example Bash Script Outline:**

```bash
#!/bin/bash
# scan-asset.sh - Generate a scan bundle for an asset

ASSET_ID="$1"
TECH_NAME="$2"
OUTPUT_FILE="scan-bundle-${ASSET_ID}.json"

# Run commands and capture output + status
LSHW_JSON=$(sudo lshw -json 2>/tmp/lshw.err)
LSHW_RC=$?
LSHW_ERR=$(cat /tmp/lshw.err)

LSBLK_JSON=$(lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT 2>/tmp/lsblk.err)
LSBLK_RC=$?
LSBLK_ERR=$(cat /tmp/lsblk.err)

LSPCI_OUT=$(lspci -vv 2>/tmp/lspci.err)
LSPCI_RC=$?
LSPCI_ERR=$(cat /tmp/lspci.err)

# ... collect other sources ...

# Assemble JSON using jq or Python
cat > "$OUTPUT_FILE" <<EOF
{
  "schema": "motherboard.scan_bundle.v1",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%6NZ)",
  "scanner": {
    "hostname": "$(hostname)",
    "user": "$(whoami)"
  },
  "intake": {
    "asset_id": "$ASSET_ID",
    "tech_name": "$TECH_NAME",
    "client_name": "",
    "cosmetic_condition": "",
    "note": ""
  },
  "sources": {
    "lshw": $LSHW_JSON,
    "lsblk": $LSBLK_JSON,
    "lspci": $(echo "$LSPCI_OUT" | jq -Rs .),
    ...
  },
  "meta": {
    "status": {
      "lshw": {"rc": $LSHW_RC, "stderr": $(echo "$LSHW_ERR" | jq -Rs .)},
      "lsblk": {"rc": $LSBLK_RC, "stderr": $(echo "$LSBLK_ERR" | jq -Rs .)},
      ...
    }
  }
}
EOF

echo "Scan bundle saved to $OUTPUT_FILE"
```

**Note:** The above is a simplified outline. A production scanner should:
- Handle JSON escaping properly
- Use `jq` or Python for robust JSON generation
- Check for missing commands
- Validate the final JSON structure
- Provide user-friendly prompts for intake metadata

### Validation Rules

The system enforces the following validation rules:

✅ **Schema Validation:**
- `schema` must equal `"motherboard.scan_bundle.v1"`
- `generated_at` must be present (ISO 8601 format)
- `scanner.hostname` and `scanner.user` must be present
- `intake.asset_id` must be present and **match the URL asset tag**
- `sources.lshw` must be present (required for drive extraction)
- `meta.status` must be present

❌ **Upload will be rejected if:**
- JSON is malformed or not valid JSON
- Schema is missing or incorrect
- `intake.asset_id` doesn't match the URL asset tag
- `sources.lshw` is missing
- File size exceeds 5MB (configurable via `MAX_LSHW_BYTES` setting)

✅ **Deduplication:**
- The system computes a SHA-256 hash of the canonical JSON
- If an identical bundle (same hash) already exists for the asset, the upload is acknowledged but not stored again
- This prevents duplicate storage of unchanged scans

### What the System Extracts

From the `sources.lshw` portion of the bundle, the system extracts:

- **Device Serial Number** (from system chassis or motherboard)
- **CPU Information** (model, cores, frequency)
- **Memory Information** (total RAM, per-slot details)
- **Storage Drives** (model, serial, capacity, logical name)
- **Graphics Cards** (model, vendor)
- **Network Interfaces** (model, MAC address)
- **Battery Information** (if present)

**Drive Records:**
- Each disk found in lshw is created as a `Drive` record
- Drives are deduplicated by serial number per asset
- Drive status can be tracked independently (present, wiped, shredded, removed)

### Managing Asset Intake

Use the "Intake Information" form to track:
- **Status**: Intake, Testing, Ready for Sale, Sold, Recycled, Returned to Client
- **Device Type**: Laptop, Desktop, Server, Tablet, Phone, Other
- **Cosmetic Grade**: A (Excellent), B (Good), C (Fair), D (Poor)
- **Cosmetic Notes**: Any scratches, dents, damage
- **Location**: Physical location (shelf, bin, warehouse)

### Tracking Drive Status

For compliance and data security:

1. Find a drive in the "Storage Drives" section
2. Click "Update Status"
3. Set status: Present, Removed, Wiped, Shredded, Returned to Client
4. Add optional notes
5. Click "Update Drive Status"

All status changes are logged in the audit trail!

### Searching for Drives

To find a drive across all assets:

**Via API:**
```bash
curl "http://localhost:8000/api/drive/by_serial/?serial=YOUR_SERIAL_HERE"
```

**Via Admin:**
1. Go to http://localhost:8000/admin/
2. Click "Drives"
3. Use the search box to search by serial, model, or asset tag

## 🔧 Common Commands

### Stop the Application
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Just Django
docker-compose logs web

# Follow logs (live)
docker-compose logs -f web
```

### Restart After Code Changes
```bash
# Django auto-reloads when you edit Python files
# But if you need to restart:
docker-compose restart web
```

### Access Django Shell
```bash
docker-compose exec web python manage.py shell
```

### Create Additional Users
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Database Migrations (after model changes)
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## 🎨 Django Admin Interface

The Django admin at http://localhost:8000/admin/ gives you:

- **Assets**: Full CRUD operations, filtering, search
- **Hardware Scans**: View all uploaded scan bundles with metadata
- **Drives**: Manage drives, search by serial
- **Asset Touches**: Complete audit trail (read-only)
- **Users**: Manage user accounts and permissions

**Pro Tip:** Use the admin for bulk operations and complex queries!

## 🔐 Security Notes

### For Development/Testing:
The default passwords are fine.

### For Production:
1. **Change all passwords in `.env`**:
   - `POSTGRES_PASSWORD`
   - `DJANGO_SUPERUSER_PASSWORD`
   - `PGADMIN_PASSWORD`

2. **Generate a new Django secret key**:
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

3. **Set DEBUG to False**:
   ```
   DJANGO_DEBUG=False
   ```

4. **Configure ALLOWED_HOSTS**:
   ```
   DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

5. **Use HTTPS** (add nginx with SSL certificates)

## 📊 Database Management

### Backup Database
```bash
docker-compose exec db pg_dump -U postgres asset_control > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T db psql -U postgres asset_control
```

### Access Database with psql
```bash
docker-compose exec db psql -U postgres -d asset_control
```

### Query Scan Bundles
```sql
-- View all scan bundles with metadata
SELECT 
  id, 
  asset_id, 
  schema, 
  generated_at, 
  tech_name, 
  bundle_hash,
  scanned_at
FROM assets_hardwarescan
ORDER BY scanned_at DESC;

-- Find duplicate scans (same bundle_hash)
SELECT 
  bundle_hash, 
  COUNT(*) as count
FROM assets_hardwarescan
WHERE bundle_hash IS NOT NULL
GROUP BY bundle_hash
HAVING COUNT(*) > 1;
```

## 🐛 Troubleshooting

### "Port 8000 is already in use"
Another application is using port 8000. Either:
- Stop the other application
- Or change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Use 8001 instead
  ```

### "Database connection failed"
Wait a few seconds - PostgreSQL might still be starting up. The Django container waits for the database to be healthy before starting.

### "Can't log in"
- Default credentials: `admin` / `admin123`
- Check the startup logs for the actual username/password
- If you changed `.env`, restart: `docker-compose down && docker-compose up`

### "Static files not loading"
Run:
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart web
```

### "Upload rejected: asset_id doesn't match"
The `intake.asset_id` field in your scan bundle JSON must exactly match the asset tag in the URL. If uploading to `/asset/666/`, the bundle must have `"intake": {"asset_id": "666", ...}`.

### "Upload rejected: schema invalid"
Ensure your scan bundle has `"schema": "motherboard.scan_bundle.v1"` at the top level, and includes all required fields (`generated_at`, `scanner`, `intake`, `sources.lshw`, `meta.status`).

### "Duplicate scan bundle"
This is normal! The system detected that an identical scan bundle (same SHA-256 hash) was already uploaded for this asset. The duplicate is not stored to save space.

## 📁 Project Structure

```
control-panel/
├── assets/                      # Main Django app
│   ├── models.py               # Database models (Asset, HardwareScan, Drive)
│   ├── views.py                # View functions (endpoints)
│   ├── forms.py                # Form validation (scan bundle schema validation)
│   ├── admin.py                # Admin interface config
│   ├── lshw_parser.py          # Hardware scan parser (extracts data from lshw)
│   ├── urls.py                 # URL routing
│   ├── migrations/             # Database migrations
│   │   ├── 0001_initial.py
│   │   └── 0002_hardwarescan_bundle_hash_*.py  # Scan bundle fields
│   └── management/
│       └── commands/
│           └── create_superuser_if_none.py  # Auto-create admin
├── config/                      # Django project settings
│   ├── settings.py             # Main configuration
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # WSGI entry point
├── templates/                   # HTML templates
│   ├── login.html
│   ├── home.html
│   └── assets/
│       └── asset_detail.html   # Shows scan bundle metadata & status
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Django container definition
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management script
├── .env                         # Environment variables (passwords)
└── README.md                    # This file!
```

## 🆚 Differences from FastAPI Version

### What's Better in Django:
✅ **Django Admin** - Free, powerful data management interface  
✅ **ORM** - No raw SQL queries, cleaner code  
✅ **Migrations** - Database schema versioning built-in  
✅ **Forms** - Automatic validation  
✅ **Auth** - Proper login sessions (no HTTP Basic Auth popup)  
✅ **Less Code** - Django handles a lot automatically  
✅ **Scan Bundles** - Comprehensive multi-source hardware data with status tracking  
✅ **Deduplication** - SHA-256 hash prevents duplicate uploads  

### What's the Same:
✅ **Auto-creates assets** on first visit  
✅ **Drive tracking** with lifecycle management  
✅ **Audit trail** for all actions  
✅ **JSON API endpoints** available  

### What's New:
🆕 **Scan Bundle Schema** - Structured, versioned JSON format  
🆕 **Per-Source Status** - See return codes and errors for each tool  
🆕 **Scanner Metadata** - Track which machine/user performed the scan  
🆕 **Intake Metadata** - Embedded in the scan bundle  
🆕 **Deduplication** - Automatic via content hashing  

## 🔗 API Endpoints

### Web Interface (Login Required):
- `GET /` - Home page with recent assets
- `GET /asset/{asset_tag}/` - Asset detail page (auto-creates)
- `POST /asset/{asset_tag}/intake/` - Update intake form
- `POST /asset/{asset_tag}/upload/` - Upload scan bundle JSON
- `POST /asset/{asset_tag}/drive/{id}/status/` - Update drive status

### JSON API (Login Required):
- `GET /api/assets/` - List all assets (JSON)
- `GET /api/drive/by_serial/?serial=XXX` - Search drives by serial (JSON)

### Admin:
- `GET /admin/` - Django admin interface

### Auth:
- `GET /login/` - Login page
- `POST /logout/` - Logout

## 📚 Learning Resources

New to Django? Check these out:

- **Django Docs**: https://docs.djangoproject.com/
- **Django Admin**: https://docs.djangoproject.com/en/5.0/ref/contrib/admin/
- **Django ORM**: https://docs.djangoproject.com/en/5.0/topics/db/queries/
- **Django Forms**: https://docs.djangoproject.com/en/5.0/topics/forms/

## 🤝 Getting Help

### View Logs
```bash
docker-compose logs -f web
```

### Check Database
```bash
docker-compose exec db psql -U postgres -d asset_control -c "SELECT COUNT(*) FROM assets_asset;"
```

### Django Shell (Python REPL)
```bash
docker-compose exec web python manage.py shell
```
Then try:
```python
from assets.models import Asset, HardwareScan, Drive

# View all assets
Asset.objects.all()

# View scan bundles
HardwareScan.objects.select_related('asset').all()

# Find scans with specific metadata
HardwareScan.objects.filter(tech_name='John Smith')

# Check for duplicate bundles
from django.db.models import Count
HardwareScan.objects.values('bundle_hash').annotate(
    count=Count('id')
).filter(count__gt=1)
```

## 🎉 Next Steps

Now that your Django app is running:

1. **Create some test assets** - Visit `/asset/TEST-001/`, `/asset/TEST-002/`, etc.
2. **Create a scanner script** - Use the bash outline above or write your own in Python
3. **Generate a scan bundle** - Run your scanner on a test machine
4. **Upload the bundle** - Test the upload flow and view the results
5. **Explore the Admin** - http://localhost:8000/admin/
6. **Customize the models** - Edit `assets/models.py` and run migrations
7. **Add more fields** - The framework makes it easy to extend

## 📝 Notes for Beginners

- **Assets auto-create**: Just type a tag and go - no need to create it first
- **Forms validate automatically**: Django checks your input
- **Audit trail logs everything**: Every action is recorded
- **Admin is your friend**: Use it to explore the database
- **Migrations track changes**: Django knows what changed in your database
- **The ORM is powerful**: You rarely need to write SQL
- **Scan bundles are deduplicated**: SHA-256 hash prevents storing duplicates
- **Per-source status helps debug**: See which tools failed and why

## 🚀 You're Ready!

Your Django Asset Control Panel is now running with full scan bundle support!

**Start here:**
1. Visit http://localhost:8000/login/
2. Login with `admin` / `admin123`
3. Create an asset (e.g., `/asset/666/`)
4. Create or obtain a scan bundle JSON file
5. Upload it and explore the detailed hardware information!

Happy tracking! 📦