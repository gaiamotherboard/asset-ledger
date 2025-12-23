#!/bin/bash
# GitHub Setup Script - 100% Terminal Based
# This script will initialize git, create a GitHub repo, and push everything

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   GitHub Setup - Control Panel Project           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI (gh) is not installed.${NC}"
    echo ""
    echo "Installing GitHub CLI..."
    echo ""

    # Detect OS and install
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command -v apt &> /dev/null; then
            echo "Detected Ubuntu/Debian..."
            type -p curl >/dev/null || sudo apt install curl -y
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh -y
        # Fedora/RHEL
        elif command -v dnf &> /dev/null; then
            echo "Detected Fedora/RHEL..."
            sudo dnf install gh -y
        else
            echo -e "${RED}Could not detect package manager. Please install 'gh' manually:${NC}"
            echo "https://github.com/cli/cli#installation"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install gh
        else
            echo -e "${RED}Homebrew not found. Please install 'gh' manually:${NC}"
            echo "https://github.com/cli/cli#installation"
            exit 1
        fi
    else
        echo -e "${RED}Unsupported OS. Please install 'gh' manually:${NC}"
        echo "https://github.com/cli/cli#installation"
        exit 1
    fi

    echo -e "${GREEN}✓ GitHub CLI installed!${NC}"
    echo ""
fi

# Check if already logged in
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}You need to authenticate with GitHub.${NC}"
    echo ""
    echo "This will open your browser to login..."
    echo ""
    read -p "Press Enter to continue..."

    gh auth login

    if ! gh auth status &> /dev/null; then
        echo -e "${RED}Authentication failed. Please try again.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Authenticated with GitHub${NC}"
echo ""

# Initialize git if not already done
if [ ! -d .git ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
else
    echo -e "${GREEN}✓ Git already initialized${NC}"
fi

# Check if there are any commits
if ! git rev-parse HEAD &> /dev/null; then
    echo -e "${YELLOW}Creating initial commit...${NC}"
    git add .
    git commit -m "Initial Django asset control panel - migrated from FastAPI

Features:
- Asset tracking with auto-creation
- Hardware scan upload (lshw parser)
- Drive lifecycle management
- Complete audit trail
- Django Admin interface
- PostgreSQL + pgAdmin
- Docker Compose setup"
    echo -e "${GREEN}✓ Initial commit created${NC}"
else
    echo -e "${GREEN}✓ Repository has commits${NC}"

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}You have uncommitted changes. Committing them...${NC}"
        git add .
        git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
        echo -e "${GREEN}✓ Changes committed${NC}"
    fi
fi

echo ""

# Ask for repository details
echo -e "${BLUE}Repository Setup:${NC}"
echo ""

read -p "Repository name (default: control-panel): " REPO_NAME
REPO_NAME=${REPO_NAME:-control-panel}

read -p "Description (default: Django Asset Tracking System): " REPO_DESC
REPO_DESC=${REPO_DESC:-"Django Asset Tracking System"}

echo ""
echo "Visibility:"
echo "  1) Public (anyone can see)"
echo "  2) Private (only you can see)"
read -p "Choose (1 or 2, default: 1): " VISIBILITY_CHOICE
VISIBILITY_CHOICE=${VISIBILITY_CHOICE:-1}

if [ "$VISIBILITY_CHOICE" == "2" ]; then
    VISIBILITY="--private"
else
    VISIBILITY="--public"
fi

echo ""
echo -e "${YELLOW}Creating GitHub repository...${NC}"
echo ""

# Create the repository
gh repo create "$REPO_NAME" \
    $VISIBILITY \
    --source=. \
    --description="$REPO_DESC" \
    --push

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              SUCCESS! 🎉                          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✓ Repository created and pushed to GitHub${NC}"
    echo ""

    # Get the repo URL
    REPO_URL=$(gh repo view --json url -q .url)

    echo -e "${BLUE}Your repository:${NC}"
    echo -e "  ${REPO_URL}"
    echo ""

    echo -e "${BLUE}Clone on your VM with:${NC}"
    echo -e "  ${YELLOW}git clone ${REPO_URL}${NC}"
    echo ""

    echo -e "${BLUE}To update later:${NC}"
    echo -e "  ${YELLOW}git add .${NC}"
    echo -e "  ${YELLOW}git commit -m 'Your message'${NC}"
    echo -e "  ${YELLOW}git push${NC}"
    echo ""

    echo -e "${GREEN}All done! Your code is now on GitHub.${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}Failed to create repository.${NC}"
    echo "This might be because:"
    echo "  1. Repository name already exists"
    echo "  2. Network connection issue"
    echo "  3. GitHub API rate limit"
    echo ""
    echo "Try running this script again or create the repo manually."
    exit 1
fi
