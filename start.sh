#!/bin/bash
# Asset Control Panel - Quick Start Script
# This script helps you manage the Django application

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Asset Control Panel - Management Script        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Function to show menu
show_menu() {
    echo -e "${GREEN}What would you like to do?${NC}"
    echo ""
    echo "  1) Start the application (first time or fresh start)"
    echo "  2) Start the application (if already built)"
    echo "  3) Stop the application"
    echo "  4) View logs (live)"
    echo "  5) Restart Django only"
    echo "  6) Open Django shell"
    echo "  7) Create a new admin user"
    echo "  8) Backup database"
    echo "  9) Show application URLs"
    echo " 10) Exit"
    echo ""
}

# Function to start app (first time)
start_fresh() {
    echo -e "${YELLOW}Building and starting all containers...${NC}"
    docker-compose up --build -d
    echo ""
    echo -e "${GREEN}✓ Application started!${NC}"
    show_urls
}

# Function to start app (quick)
start_quick() {
    echo -e "${YELLOW}Starting containers...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✓ Application started!${NC}"
    show_urls
}

# Function to stop app
stop_app() {
    echo -e "${YELLOW}Stopping all containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Application stopped${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${YELLOW}Showing live logs (Ctrl+C to exit)...${NC}"
    docker-compose logs -f web
}

# Function to restart Django
restart_django() {
    echo -e "${YELLOW}Restarting Django container...${NC}"
    docker-compose restart web
    echo -e "${GREEN}✓ Django restarted${NC}"
}

# Function to open shell
open_shell() {
    echo -e "${YELLOW}Opening Django shell...${NC}"
    docker-compose exec web python manage.py shell
}

# Function to create user
create_user() {
    echo -e "${YELLOW}Creating new admin user...${NC}"
    docker-compose exec web python manage.py createsuperuser
}

# Function to backup database
backup_db() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${YELLOW}Backing up database to ${BACKUP_FILE}...${NC}"
    docker-compose exec -T db pg_dump -U postgres asset_control > "$BACKUP_FILE"
    echo -e "${GREEN}✓ Database backed up to ${BACKUP_FILE}${NC}"
}

# Function to show URLs
show_urls() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Application URLs:${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}Main App:${NC}       http://localhost:8000/"
    echo -e "  ${BLUE}Login:${NC}          http://localhost:8000/login/"
    echo -e "  ${BLUE}Django Admin:${NC}   http://localhost:8000/admin/"
    echo -e "  ${BLUE}pgAdmin:${NC}        http://localhost:5050/"
    echo ""
    echo -e "  ${YELLOW}Default Credentials:${NC}"
    echo -e "  ${YELLOW}Username:${NC} admin"
    echo -e "  ${YELLOW}Password:${NC} admin123"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-10): " choice
    echo ""

    case $choice in
        1)
            start_fresh
            ;;
        2)
            start_quick
            ;;
        3)
            stop_app
            ;;
        4)
            view_logs
            ;;
        5)
            restart_django
            ;;
        6)
            open_shell
            ;;
        7)
            create_user
            ;;
        8)
            backup_db
            ;;
        9)
            show_urls
            ;;
        10)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            echo ""
            ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    clear
done
