# 🚀 QUICK START - Asset Control Panel

## For Complete Beginners

### Step 1: Open Terminal
```bash
cd ~/Desktop/control-panel
```

### Step 2: Start Everything
```bash
docker-compose up --build
```

Wait for this message:
```
✓ Superuser 'admin' created successfully!
  Login at http://localhost:8000/admin/ or http://localhost:8000/login/
  Username: admin
  Password: admin123
```

### Step 3: Open Your Browser

Go to: **http://localhost:8000/login/**

- Username: `admin`
- Password: `admin123`

### Step 4: Create Your First Asset

1. Type an asset tag (like `TEST-001`)
2. Click "Go to Asset"
3. Done! The asset is created automatically.

### Step 5: Upload Hardware Info (Optional)

On a Linux computer, run:
```bash
sudo lshw -json > hardware.json
```

Then upload that file on the asset page.

---

## Common Commands

### Stop the app:
```bash
docker-compose down
```

### Start the app (after first time):
```bash
docker-compose up
```

### View logs:
```bash
docker-compose logs -f web
```

### Use the helper script:
```bash
./start.sh
```

---

## Important URLs

| What | URL | Credentials |
|------|-----|-------------|
| **Login** | http://localhost:8000/login/ | admin / admin123 |
| **Home** | http://localhost:8000/ | (after login) |
| **Django Admin** | http://localhost:8000/admin/ | admin / admin123 |
| **pgAdmin** | http://localhost:5050/ | admin@example.com / admin123 |

---

## Need Help?

1. **Read the full README**: `README.md`
2. **Check logs**: `docker-compose logs web`
3. **Stop and restart**: `docker-compose down && docker-compose up`

---

## What This App Does

- **Track IT Assets**: Computers, servers, phones, tablets
- **Upload Hardware Scans**: Automatic detection of CPU, RAM, drives
- **Manage Drives**: Track drive status (present, wiped, shredded, etc.)
- **Audit Trail**: Every action is logged
- **Auto-Create**: Assets are created when you first visit them

---

## First Time Checklist

- [ ] Run `docker-compose up --build`
- [ ] Wait for "Superuser created" message
- [ ] Visit http://localhost:8000/login/
- [ ] Login with admin / admin123
- [ ] Create a test asset (TEST-001)
- [ ] Explore the Django Admin at /admin/
- [ ] Success! 🎉

---

## Pro Tips

- **Assets auto-create**: No need to manually create them first
- **Use the admin**: http://localhost:8000/admin/ for advanced features
- **Forms validate**: Django checks your input automatically
- **Everything is logged**: Check the "Audit Trail" section
- **Search drives**: Use the admin to search by serial number

---

## Troubleshooting

### "Port already in use"
Another app is using port 8000. Stop it or change the port in docker-compose.yml

### "Can't connect to database"
Wait 10 seconds. PostgreSQL takes time to start.

### "Can't log in"
Default is admin / admin123. Check the startup logs for confirmation.

### "Static files missing"
Run: `docker-compose exec web python manage.py collectstatic --noinput`

---

## Next Steps

1. **Create test assets** - Try TEST-001, TEST-002, etc.
2. **Upload a hardware scan** - Run lshw on Linux
3. **Explore the admin** - Powerful interface at /admin/
4. **Read the full README** - Detailed documentation
5. **Customize** - Edit models, add features

---

## You're Ready! 🎉

**Start here:** http://localhost:8000/login/

Login: `admin` / `admin123`

Have fun tracking your assets!