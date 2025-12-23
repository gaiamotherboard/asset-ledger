#!/bin/bash
# Bundle all code into a single file for AI/chatbot review
# This creates a comprehensive text file with all your project code

OUTPUT_FILE="code-bundle-$(date +%Y%m%d-%H%M%S).txt"

echo "Creating code bundle: $OUTPUT_FILE"
echo ""

cat > "$OUTPUT_FILE" << 'EOF'
================================================================================
DJANGO ASSET CONTROL PANEL - CODE BUNDLE FOR REVIEW
================================================================================
Generated: $(date)
GitHub: https://github.com/gaiamotherboard/control-panel

This bundle contains all source code for review by AI assistants or developers.

TABLE OF CONTENTS:
1. Project Structure
2. Configuration Files
3. Django Settings & URLs
4. Django Models (Database Schema)
5. Django Views (Business Logic)
6. Django Forms (Validation)
7. Django Admin Configuration
8. Utility Modules (LSHW Parser)
9. Management Commands
10. HTML Templates
11. Documentation

================================================================================

EOF

# Add project structure
echo "1. PROJECT STRUCTURE" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
tree -I '__pycache__|*.pyc|staticfiles|media|*.sql|postgres_data|pgadmin_data' -L 3 >> "$OUTPUT_FILE" 2>/dev/null || find . -type f -not -path '*/\.*' -not -path '*/__pycache__/*' -not -path '*/staticfiles/*' | head -50 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to add a file with header
add_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo "=================================================================================" >> "$OUTPUT_FILE"
        echo "FILE: $file" >> "$OUTPUT_FILE"
        echo "DESCRIPTION: $description" >> "$OUTPUT_FILE"
        echo "=================================================================================" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
}

# Configuration Files
echo "" >> "$OUTPUT_FILE"
echo "2. CONFIGURATION FILES" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "requirements.txt" "Python dependencies"
add_file "docker-compose.yml" "Docker orchestration configuration"
add_file "Dockerfile" "Django container build instructions"
add_file ".env" "Environment variables (sanitized - no real passwords shown)"

# Django Core
echo "" >> "$OUTPUT_FILE"
echo "3. DJANGO SETTINGS & URLS" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "config/settings.py" "Main Django configuration"
add_file "config/urls.py" "Root URL routing"
add_file "config/wsgi.py" "WSGI application entry point"
add_file "manage.py" "Django management script"

# Models
echo "" >> "$OUTPUT_FILE"
echo "4. DJANGO MODELS (DATABASE SCHEMA)" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/models.py" "Database models - Asset, HardwareScan, Drive, AssetTouch"

# Views
echo "" >> "$OUTPUT_FILE"
echo "5. DJANGO VIEWS (BUSINESS LOGIC)" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/views.py" "View functions - handles all user interactions"
add_file "assets/urls.py" "Assets app URL routing"

# Forms
echo "" >> "$OUTPUT_FILE"
echo "6. DJANGO FORMS (VALIDATION)" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/forms.py" "Form classes with validation logic"

# Admin
echo "" >> "$OUTPUT_FILE"
echo "7. DJANGO ADMIN CONFIGURATION" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/admin.py" "Django admin interface customization"

# Utilities
echo "" >> "$OUTPUT_FILE"
echo "8. UTILITY MODULES" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/lshw_parser.py" "Hardware scan parser - extracts CPU, RAM, drives from lshw JSON"

# Management Commands
echo "" >> "$OUTPUT_FILE"
echo "9. MANAGEMENT COMMANDS" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "assets/management/commands/create_superuser_if_none.py" "Auto-create admin user on startup"

# App Config
add_file "assets/apps.py" "Assets app configuration"

# Templates
echo "" >> "$OUTPUT_FILE"
echo "10. HTML TEMPLATES" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "templates/login.html" "Login page template"
add_file "templates/home.html" "Home page with asset list"
add_file "templates/assets/asset_detail.html" "Main asset detail page with all features"

# Documentation
echo "" >> "$OUTPUT_FILE"
echo "11. DOCUMENTATION" >> "$OUTPUT_FILE"
echo "==================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

add_file "README.md" "Complete project documentation"
add_file "QUICKSTART.md" "Quick start guide"
add_file "START-HERE.md" "Personal getting started guide"

# Summary stats
echo "" >> "$OUTPUT_FILE"
echo "=================================================================================" >> "$OUTPUT_FILE"
echo "SUMMARY STATISTICS" >> "$OUTPUT_FILE"
echo "=================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Python files:" >> "$OUTPUT_FILE"
find . -name "*.py" -not -path '*/__pycache__/*' | wc -l >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Lines of Python code:" >> "$OUTPUT_FILE"
find . -name "*.py" -not -path '*/__pycache__/*' -exec wc -l {} + | tail -1 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "HTML templates:" >> "$OUTPUT_FILE"
find . -name "*.html" | wc -l >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Questions for reviewers
cat >> "$OUTPUT_FILE" << 'EOF'

=================================================================================
QUESTIONS FOR CODE REVIEWERS:
=================================================================================

1. ARCHITECTURE & DESIGN:
   - Is the Django app structure well-organized?
   - Are the models designed efficiently (Asset, HardwareScan, Drive, AssetTouch)?
   - Is the separation of concerns appropriate (views, forms, models)?

2. SECURITY:
   - Are there any security vulnerabilities?
   - Is authentication handled properly?
   - Are file uploads validated securely?
   - Is the audit trail (AssetTouch) comprehensive enough?

3. DATABASE:
   - Are the model relationships optimal?
   - Should any indexes be added?
   - Is the unique_together constraint on Drive appropriate?

4. CODE QUALITY:
   - Are there any code smells or anti-patterns?
   - Is error handling adequate?
   - Are docstrings clear and helpful?

5. FEATURES:
   - The lshw parser extracts hardware info - is the logic sound?
   - Auto-creation of assets on first visit - good pattern or problematic?
   - Drive lifecycle tracking - any missing states or edge cases?

6. PERFORMANCE:
   - Are there any N+1 query issues?
   - Should any views use select_related() or prefetch_related()?
   - Is the hardware scan upload (5MB limit) appropriate?

7. DJANGO BEST PRACTICES:
   - Are we following Django conventions?
   - Is the admin configuration well-designed?
   - Are forms using Django's validation properly?

8. DEPLOYMENT:
   - Is the Docker setup production-ready?
   - Any issues with the docker-compose configuration?
   - Should we add nginx for production?

9. TESTING:
   - What tests should be added?
   - Any critical paths that need test coverage?

10. IMPROVEMENTS:
    - What features or refactors would you suggest?
    - Are there any Django packages we should consider?

=================================================================================
END OF CODE BUNDLE
=================================================================================
EOF

echo "✓ Code bundle created: $OUTPUT_FILE"
echo ""
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo "Lines: $(wc -l < "$OUTPUT_FILE")"
echo ""
echo "You can now:"
echo "  1. Share this file with AI chatbots (Claude, ChatGPT, etc.)"
echo "  2. Send to other developers for review"
echo "  3. Upload to code review platforms"
echo ""
echo "To view the file:"
echo "  less $OUTPUT_FILE"
echo ""
