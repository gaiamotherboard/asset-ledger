# 🚀 VM DEPLOYMENT GUIDE

## 100% Terminal - No Browser Needed!

This guide shows you how to push your Django app to GitHub and deploy it on your VM, all from the terminal.

---

## 📋 Prerequisites

- Your VM accessible via SSH
- This project directory on your desktop
- Terminal open

---

## 🎯 SUPER QUICK METHOD (3 Commands!)

### Step 1: Push to GitHub (One Command!)

```bash
cd ~/Desktop/control-panel
./setup-github.sh
```

**What it does:**
- Installs GitHub CLI if needed
- Logs you into GitHub (browser popup)
- Creates git repository
- Creates GitHub repo
- Pushes everything automatically

**Follow the prompts:**
- Repository name: `control-panel` (or whatever you want)
- Description: `Django Asset Tracking System`
- Public or Private: Your choice
- **Done!** ✅

---

### Step 2: Deploy to VM (One Command!)

```bash
./deploy-to-vm.sh
```

**What it does:**
- Asks for VM details (user, IP, port)
- Tests SSH connection
- Clones from GitHub to VM
- Installs Docker if needed
- Starts the application
- **Done!** ✅

**You'll be asked:**
- VM username (e.g., `ubuntu`, `root`, `stephen`)
- VM IP address (e.g., `192.168.1.100`)
- SSH port (default: 22)
- Directory on VM (default: `~/control-panel`)

---

### Step 3: Access Your App!

```
http://YOUR_VM_IP:8000/
```

**Login:**
- Username: `admin`
- Password: `admin123`

---

## 🔧 Manual Method (If Scripts Don't Work)

### Step 1: Install GitHub CLI

```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y
```

### Step 2: Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts (choose GitHub.com, HTTPS, Yes to authenticate)

### Step 3: Create Repo and Push

```bash
cd ~/Desktop/control-panel

# Initialize git
git init
git add .
git commit -m "Initial Django asset control panel"

# Create GitHub repo and push (one command!)
gh repo create control-panel --public --source=. --push
```

### Step 4: Deploy to VM

```bash
# SSH into your VM
ssh user@your-vm-ip

# Clone the repository
git clone https://github.com/YOUR_USERNAME/control-panel.git
cd control-panel

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install docker-compose
sudo apt-get update
sudo apt-get install -y docker-compose

# Update .env with your VM's IP
nano .env
# Change: DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_VM_IP

# Start the application
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

---

## 🔄 Updating After Changes

### Method 1: Git Workflow (Recommended)

**On your desktop:**
```bash
cd ~/Desktop/control-panel

# Make your changes to files...

# Commit and push
git add .
git commit -m "Description of changes"
git push
```

**On your VM:**
```bash
ssh user@your-vm-ip
cd ~/control-panel

# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build -d

# Check logs
docker-compose logs -f web
```

### Method 2: Direct Sync with rsync

**From your desktop:**
```bash
rsync -avz -e ssh ~/Desktop/control-panel/ user@your-vm-ip:~/control-panel/
ssh user@your-vm-ip "cd ~/control-panel && docker-compose up --build -d"
```

---

## 🖥️ Editing Files on VM (VS Code Remote SSH)

This is THE BEST way to work with remote files!

### Setup (One Time):

1. **Install VS Code Extension:**
   - Open VS Code
   - Extensions (Ctrl+Shift+X)
   - Search: "Remote - SSH"
   - Install it

2. **Connect to VM:**
   - Press F1
   - Type: "Remote-SSH: Connect to Host"
   - Enter: `user@your-vm-ip`
   - Enter password or use SSH key

3. **Open Project:**
   - File → Open Folder
   - Navigate to `~/control-panel`
   - **Now you're editing directly on the VM!**

4. **Benefits:**
   - I can still help you (files are in workspace)
   - Edit directly on VM
   - Terminal runs on VM
   - No need to sync files
   - Django auto-reloads on changes

---

## 📊 Useful VM Commands

### Check if app is running:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose ps"
```

### View logs:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose logs -f web"
```

### Stop the app:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose down"
```

### Start the app:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose up -d"
```

### Restart Django only:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose restart web"
```

### Access Django shell on VM:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose exec web python manage.py shell"
```

### Backup database on VM:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose exec -T db pg_dump -U postgres asset_control > backup.sql"
```

---

## 🔐 Security Checklist for VM

Before going to production, update `.env` on the VM:

```bash
ssh user@your-vm-ip
cd ~/control-panel
nano .env
```

**Change these:**
1. `POSTGRES_PASSWORD` - Use a strong password
2. `DJANGO_SECRET_KEY` - Generate new: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
3. `DJANGO_SUPERUSER_PASSWORD` - Change from default
4. `DJANGO_ALLOWED_HOSTS` - Add your domain/IP
5. `DJANGO_DEBUG=False` - Set to False in production

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## 🌐 Accessing from Anywhere

### Option 1: VM with Public IP
If your VM has a public IP, access it directly:
```
http://YOUR_PUBLIC_IP:8000/
```

### Option 2: SSH Tunnel (VM on Private Network)
If VM is on private network, create SSH tunnel:
```bash
ssh -L 8000:localhost:8000 user@your-vm-ip
```
Then access: `http://localhost:8000/`

### Option 3: Domain Name + Nginx (Production)
For production with custom domain:
1. Point domain to VM IP
2. Add nginx for SSL/HTTPS
3. Use Let's Encrypt for SSL certificate

---

## 🆘 Troubleshooting

### "Permission denied (publickey)"
Set up SSH keys:
```bash
ssh-copy-id user@your-vm-ip
```

### "Port 8000 already in use"
Check what's using it:
```bash
ssh user@your-vm-ip "sudo lsof -i :8000"
```

### "Docker permission denied"
Log out and back in after Docker install:
```bash
ssh user@your-vm-ip
sudo usermod -aG docker $USER
exit
# SSH back in
```

### "Can't connect to database"
Wait 10 seconds, check logs:
```bash
ssh user@your-vm-ip "cd ~/control-panel && docker-compose logs db"
```

### "GitHub CLI not working"
Install manually: https://github.com/cli/cli#installation

---

## 🎯 Quick Command Reference

```bash
# Push to GitHub
./setup-github.sh

# Deploy to VM
./deploy-to-vm.sh

# SSH to VM
ssh user@your-vm-ip

# View VM logs
ssh user@your-vm-ip "cd ~/control-panel && docker-compose logs -f"

# Restart on VM
ssh user@your-vm-ip "cd ~/control-panel && docker-compose restart web"

# Update VM from Git
ssh user@your-vm-ip "cd ~/control-panel && git pull && docker-compose up --build -d"
```

---

## 🎉 You're Ready!

**Run these two commands:**
```bash
./setup-github.sh
./deploy-to-vm.sh
```

**Then access:**
```
http://YOUR_VM_IP:8000/
```

**Login with:** `admin` / `admin123`

That's it! Your Django app is now on GitHub and running on your VM! 🚀