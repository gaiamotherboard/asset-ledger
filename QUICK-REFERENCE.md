# Quick Reference Guide - Asset Management System

**Last Updated:** January 2024  
**Quick Start Time:** 5 minutes

---

## 🚀 Get Started Right Now

### 1. Start the Development Environment (30 seconds)

```bash
cd ~/Desktop/control-panel
docker compose --profile dev up -d --build
```

Wait for services to start (~30 seconds), then verify:

```bash
docker compose ps
```

You should see: `web`, `db`, and `pgadmin` all running.

---

### 2. Run Unit Tests (1 minute)

```bash
./run-tests.sh
```

**Expected Result:** ✅ All 13 tests pass

If tests fail, check:
- Docker services are running
- Database migrations applied

---

### 3. Create Admin User (30 seconds)

```bash
docker compose exec web python manage.py createsuperuser
```

Enter:
- Username: `admin`
- Email: (your email)
- Password: (your password)

---

### 4. Access the Application (now!)

Open in your browser:
- **Main App:** http://localhost:8001/
- **Admin Panel:** http://localhost:8001/admin/
- **pgAdmin:** http://localhost:5050/ (email: admin@admin.com, password: admin)

---

## 🧪 Quick Validation Test (5 minutes)

### Test Memory Slot Display

1. **Create test asset:**
   - Visit: http://localhost:8001/asset/TEST-001/

2. **Upload sample LSHW JSON:**
   - Create file `test-lshw.json` with this content:

```json
{
  "id": "computer",
  "class": "system",
  "serial": "TESTSERIAL123",
  "children": [{
    "id": "core",
    "class": "bus",
    "children": [{
      "id": "cpu",
      "class": "processor",
      "product": "Intel Core i5-8250U"
    }, {
      "id": "memory",
      "class": "memory",
      "description": "System Memory",
      "size": 17179869184,
      "children": [{
        "id": "bank:0",
        "class": "memory",
        "slot": "DIMM A",
        "size": 8589934592,
        "vendor": "Samsung",
        "product": "M471A1K43CB1-CTD",
        "serial": "MEM001"
      }, {
        "id": "bank:1",
        "class": "memory",
        "slot": "DIMM B",
        "size": 8589934592,
        "vendor": "Crucial",
        "product": "CT8G4SFRA266",
        "serial": "MEM002"
      }]
    }, {
      "id": "storage",
      "class": "storage",
      "children": [{
        "id": "disk",
        "class": "disk",
        "logicalname": "/dev/sda",
        "size": 256060514304,
        "product": "Samsung SSD 850",
        "serial": "S2RBNX0J123456Z"
      }]
    }]
  }]
}
```

3. **Upload the file** on the asset detail page

4. **Verify you see:**
   - ✅ Total RAM: "16 GB"
   - ✅ Memory Slots: 2 slots showing
   - ✅ Each slot: "8.0 GB"
   - ✅ Vendor and product info displayed
   - ✅ Drive detected: Samsung SSD 850, 256.0 GB
   - ✅ Warning banner: "First-class hard drive detected"

**If all checks pass:** ✅ System working perfectly!

---

## 📁 Key Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `run-tests.sh` | Run unit tests | Before any deployment |
| `VALIDATION-CHECKLIST.md` | Full test scenarios | Before production |
| `PRODUCTION-HARDENING.md` | Deployment guide | When deploying to production |
| `IMPLEMENTATION-SUMMARY.md` | Complete overview | Understanding the system |
| `assets/lshw_parser.py` | LSHW parsing logic | Understanding memory/drive parsing |
| `assets/views.py` | Main application logic | Understanding workflows |
| `assets/models.py` | Database schema | Understanding data structure |
| `templates/assets/asset_detail.html` | Main UI | UI customization |

---

## 🔍 Common Tasks

### View Logs

```bash
# All services
docker compose logs -f

# Just web application
docker compose logs -f web

# Last 50 lines
docker compose logs --tail=50 web
```

### Database Access

```bash
# PostgreSQL shell
docker compose exec db psql -U postgres -d assetdb

# Common queries
SELECT COUNT(*) FROM assets_asset;
SELECT COUNT(*) FROM assets_drive;
SELECT COUNT(*) FROM assets_hardwarescan;
```

### Reset Everything

```bash
# Stop and remove all data
docker compose down -v

# Start fresh
docker compose --profile dev up -d --build

# Create superuser again
docker compose exec web python manage.py createsuperuser
```

### Update Code

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker compose --profile dev up -d --build

# Run migrations
docker compose exec web python manage.py migrate
```

---

## 🐛 Troubleshooting

### Problem: Can't access http://localhost:8001/

**Solution:**
```bash
# Check if services are running
docker compose ps

# If not running, start them
docker compose --profile dev up -d --build

# Check logs for errors
docker compose logs web
```

---

### Problem: Tests fail with "database not found"

**Solution:**
```bash
# Run migrations
docker compose exec web python manage.py migrate

# Try tests again
./run-tests.sh
```

---

### Problem: Memory slots not showing

**Checklist:**
1. ✅ LSHW JSON has memory nodes with class="memory"
2. ✅ Memory nodes have size field (in bytes)
3. ✅ Latest scan uploaded successfully (check activity log)
4. ✅ No template errors in browser console

**Debug:**
```bash
# Check what was parsed
docker compose exec web python manage.py shell

>>> from assets.models import HardwareScan
>>> scan = HardwareScan.objects.latest('scanned_at')
>>> print(scan.summary)  # Should show RAM info
```

---

### Problem: Drives not appearing

**Common Causes:**
1. Drive has no serial number (skipped to prevent duplicates)
2. Drive is ephemeral (mmcblk*, loop*, sr*) and filtered
3. LSHW JSON missing storage nodes

**Check:**
```bash
# Look at raw drive data
docker compose exec db psql -U postgres -d assetdb -c "SELECT serial, logicalname, model FROM assets_drive;"
```

---

## 📊 Quick Stats Queries

```bash
# Connect to database
docker compose exec db psql -U postgres -d assetdb
```

```sql
-- Total assets
SELECT COUNT(*) FROM assets_asset;

-- Assets by status
SELECT status, COUNT(*) FROM assets_asset GROUP BY status;

-- Total drives
SELECT COUNT(*) FROM assets_drive;

-- Drives by status
SELECT status, COUNT(*) FROM assets_drive GROUP BY status;

-- Most recent scans
SELECT a.asset_tag, hs.scanned_at 
FROM assets_hardwarescan hs 
JOIN assets_asset a ON hs.asset_id = a.id 
ORDER BY hs.scanned_at DESC 
LIMIT 10;
```

---

## 🎯 Next Steps Flowchart

```
START HERE
    |
    v
[✅] Start Docker Compose
    |
    v
[✅] Run ./run-tests.sh
    |
    v
    Tests Pass?
    |
    +-- NO --> Check logs, fix issues
    |
    +-- YES
        |
        v
[✅] Create superuser
    |
    v
[✅] Access http://localhost:8001/
    |
    v
[✅] Upload test LSHW JSON
    |
    v
[✅] Verify memory slots display
    |
    v
    Everything works?
    |
    +-- NO --> Review IMPLEMENTATION-SUMMARY.md
    |
    +-- YES
        |
        v
    Ready for production?
    |
    +-- NO --> Continue testing with VALIDATION-CHECKLIST.md
    |
    +-- YES --> Follow PRODUCTION-HARDENING.md
```

---

## 🔐 Production Deployment (Quick)

**DO NOT deploy without reading PRODUCTION-HARDENING.md first!**

Minimum requirements:
1. ✅ Change SECRET_KEY
2. ✅ Set DEBUG=False
3. ✅ Configure ALLOWED_HOSTS
4. ✅ Use strong database password
5. ✅ Set up SSL/TLS certificates
6. ✅ Remove pgAdmin from production
7. ✅ Configure backups

**Quick production start:**

```bash
# Generate secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Create .env file
cat > .env << EOF
SECRET_KEY='your-generated-key-here'
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DB_NAME=assetdb_prod
DB_USER=assetdb_user
DB_PASSWORD=strong_random_password
EOF

# Use production compose file (after creating it per PRODUCTION-HARDENING.md)
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 📞 Getting Help

### Check in Order:

1. **This file** - Common tasks and quick fixes
2. **Application logs** - `docker compose logs -f web`
3. **IMPLEMENTATION-SUMMARY.md** - System overview and architecture
4. **VALIDATION-CHECKLIST.md** - Specific test scenarios
5. **PRODUCTION-HARDENING.md** - Deployment and security
6. **Django docs** - https://docs.djangoproject.com/

### Quick Diagnosis:

```bash
# System health check
echo "=== Docker Status ==="
docker compose ps

echo -e "\n=== Web Logs (last 20 lines) ==="
docker compose logs --tail=20 web

echo -e "\n=== Database Status ==="
docker compose exec db psql -U postgres -c "SELECT version();"

echo -e "\n=== Disk Space ==="
df -h | grep -E "(Filesystem|/dev/)"

echo -e "\n=== Asset Count ==="
docker compose exec db psql -U postgres -d assetdb -c "SELECT COUNT(*) FROM assets_asset;"
```

---

## ✅ Daily Checklist (Production)

Morning:
- [ ] Check system is accessible
- [ ] Review error logs (last 24h)
- [ ] Verify backup completed

Weekly:
- [ ] Check disk space
- [ ] Review database growth
- [ ] Update dependencies (if needed)

Monthly:
- [ ] Test backup restore
- [ ] Review audit trail
- [ ] Performance check

---

## 📝 Cheat Sheet

| Task | Command |
|------|---------|
| Start system | `docker compose --profile dev up -d` |
| Stop system | `docker compose down` |
| View logs | `docker compose logs -f web` |
| Run tests | `./run-tests.sh` |
| Shell access | `docker compose exec web bash` |
| Database shell | `docker compose exec db psql -U postgres -d assetdb` |
| Django shell | `docker compose exec web python manage.py shell` |
| Migrations | `docker compose exec web python manage.py migrate` |
| Create user | `docker compose exec web python manage.py createsuperuser` |
| Restart web | `docker compose restart web` |
| Full reset | `docker compose down -v && docker compose --profile dev up -d --build` |

---

**Remember:** All 13 unit tests should pass before any deployment!

**Need more details?** Check `IMPLEMENTATION-SUMMARY.md` for complete information.

**Ready for production?** Follow `PRODUCTION-HARDENING.md` step by step.

**Happy asset tracking! 🎉**