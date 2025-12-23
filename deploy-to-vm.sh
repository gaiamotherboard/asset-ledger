#!/bin/bash
# Deploy to VM Script
# This script helps you deploy the control panel to your remote VM

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Deploy Control Panel to VM                      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Check if git repo exists
if [ ! -d .git ]; then
    echo -e "${RED}Error: This is not a git repository.${NC}"
    echo "Please run ./setup-github.sh first to create the GitHub repo."
    exit 1
fi

# Get VM details
echo -e "${YELLOW}Enter your VM details:${NC}"
echo ""

read -p "VM username (e.g., ubuntu, root): " VM_USER
if [ -z "$VM_USER" ]; then
    echo -e "${RED}Username is required${NC}"
    exit 1
fi

read -p "VM IP address or hostname: " VM_HOST
if [ -z "$VM_HOST" ]; then
    echo -e "${RED}Host is required${NC}"
    exit 1
fi

read -p "SSH port (default: 22): " VM_PORT
VM_PORT=${VM_PORT:-22}

read -p "Directory on VM (default: ~/control-panel): " VM_DIR
VM_DIR=${VM_DIR:-"~/control-panel"}

echo ""
echo -e "${BLUE}Deployment Configuration:${NC}"
echo -e "  User: ${YELLOW}${VM_USER}${NC}"
echo -e "  Host: ${YELLOW}${VM_HOST}${NC}"
echo -e "  Port: ${YELLOW}${VM_PORT}${NC}"
echo -e "  Directory: ${YELLOW}${VM_DIR}${NC}"
echo ""

read -p "Is this correct? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${YELLOW}Testing SSH connection...${NC}"

if ssh -p "$VM_PORT" -o ConnectTimeout=5 "${VM_USER}@${VM_HOST}" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo ""
    echo "Please check:"
    echo "  1. VM is running and accessible"
    echo "  2. SSH credentials are correct"
    echo "  3. SSH keys are set up (or you'll be prompted for password)"
    exit 1
fi

echo ""
echo -e "${YELLOW}Deployment Method:${NC}"
echo "  1) Clone from GitHub (recommended - uses your GitHub repo)"
echo "  2) Direct copy via rsync (copies files directly)"
echo ""
read -p "Choose method (1 or 2): " DEPLOY_METHOD

if [ "$DEPLOY_METHOD" == "1" ]; then
    # GitHub clone method
    echo ""
    echo -e "${YELLOW}Getting GitHub repository URL...${NC}"

    REPO_URL=$(git config --get remote.origin.url)

    if [ -z "$REPO_URL" ]; then
        echo -e "${RED}No GitHub remote found.${NC}"
        echo "Please run ./setup-github.sh first."
        exit 1
    fi

    echo -e "${GREEN}✓ Repository URL: ${REPO_URL}${NC}"
    echo ""

    echo -e "${YELLOW}Deploying to VM via GitHub clone...${NC}"

    ssh -p "$VM_PORT" "${VM_USER}@${VM_HOST}" bash -s << EOF
set -e

echo "Checking for git..."
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

echo "Checking for docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    rm get-docker.sh
    echo "Docker installed. You may need to log out and back in."
fi

echo "Checking for docker-compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

echo "Cloning repository..."
if [ -d "${VM_DIR}" ]; then
    echo "Directory exists. Pulling latest changes..."
    cd ${VM_DIR}
    git pull
else
    git clone ${REPO_URL} ${VM_DIR}
    cd ${VM_DIR}
fi

echo "Setting up .env file..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
# Database settings
POSTGRES_DB=asset_control
POSTGRES_PASSWORD=change_this_password_in_production
DATABASE_URL=postgresql://postgres:change_this_password_in_production@db:5432/asset_control

# Django settings
DJANGO_SECRET_KEY=change-this-to-something-random-and-long
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,${VM_HOST}

# Initial admin user
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin123
DJANGO_SUPERUSER_EMAIL=admin@example.com

# pgAdmin settings
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin123

# Upload settings
MAX_LSHW_BYTES=5242880
ENVEOF
    echo "✓ .env file created (please customize it!)"
else
    echo "✓ .env file already exists"
fi

echo "Starting Docker containers..."
docker-compose up --build -d

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Access your application at:"
echo "  http://${VM_HOST}:8000/"
echo ""
echo "View logs with:"
echo "  docker-compose logs -f web"
EOF

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║              DEPLOYMENT SUCCESS! 🎉               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}Your application is now running on the VM!${NC}"
        echo ""
        echo -e "${BLUE}Access it at:${NC}"
        echo -e "  ${YELLOW}http://${VM_HOST}:8000/${NC}"
        echo ""
        echo -e "${BLUE}Login credentials:${NC}"
        echo -e "  Username: ${YELLOW}admin${NC}"
        echo -e "  Password: ${YELLOW}admin123${NC}"
        echo ""
        echo -e "${BLUE}To view logs:${NC}"
        echo -e "  ${YELLOW}ssh -p ${VM_PORT} ${VM_USER}@${VM_HOST}${NC}"
        echo -e "  ${YELLOW}cd ${VM_DIR}${NC}"
        echo -e "  ${YELLOW}docker-compose logs -f web${NC}"
        echo ""
        echo -e "${BLUE}To update later:${NC}"
        echo -e "  ${YELLOW}ssh -p ${VM_PORT} ${VM_USER}@${VM_HOST}${NC}"
        echo -e "  ${YELLOW}cd ${VM_DIR}${NC}"
        echo -e "  ${YELLOW}git pull${NC}"
        echo -e "  ${YELLOW}docker-compose up --build -d${NC}"
        echo ""
    else
        echo -e "${RED}Deployment failed. Check the error messages above.${NC}"
        exit 1
    fi

elif [ "$DEPLOY_METHOD" == "2" ]; then
    # rsync method
    echo ""
    echo -e "${YELLOW}Deploying to VM via rsync...${NC}"

    # Create directory on VM
    ssh -p "$VM_PORT" "${VM_USER}@${VM_HOST}" "mkdir -p ${VM_DIR}"

    # Sync files
    rsync -avz --progress \
        -e "ssh -p ${VM_PORT}" \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude 'staticfiles' \
        --exclude 'media' \
        ./ "${VM_USER}@${VM_HOST}:${VM_DIR}/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Files synced to VM${NC}"

        # Set up and start on VM
        ssh -p "$VM_PORT" "${VM_USER}@${VM_HOST}" bash -s << EOF
set -e
cd ${VM_DIR}

echo "Checking for docker..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    rm get-docker.sh
fi

echo "Checking for docker-compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

echo "Starting Docker containers..."
docker-compose up --build -d

echo ""
echo "✓ Deployment complete!"
echo "Access at: http://${VM_HOST}:8000/"
EOF

        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║              DEPLOYMENT SUCCESS! 🎉               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}Access it at:${NC}"
        echo -e "  ${YELLOW}http://${VM_HOST}:8000/${NC}"
        echo ""
    else
        echo -e "${RED}rsync failed. Check the error messages above.${NC}"
        exit 1
    fi

else
    echo -e "${RED}Invalid choice.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Pro tip: To continue editing and syncing changes:${NC}"
echo ""
echo "Method 1 - Use Git (recommended):"
echo "  1. Make changes locally"
echo "  2. git add . && git commit -m 'message' && git push"
echo "  3. On VM: git pull && docker-compose up --build -d"
echo ""
echo "Method 2 - Use VS Code Remote SSH:"
echo "  1. Install 'Remote - SSH' extension in VS Code"
echo "  2. Connect to ${VM_USER}@${VM_HOST}"
echo "  3. Open ${VM_DIR} folder"
echo "  4. Edit directly on VM!"
echo ""
