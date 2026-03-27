#!/bin/bash

# TeqMates Resort Management System - Pre-Deployment Verification Script
# This script checks if all components are ready for deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}     TeqMates Resort - Pre-Deployment Verification Script     ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Script Directory: ${YELLOW}$SCRIPT_DIR${NC}"
echo -e "${BLUE}Project Root: ${YELLOW}$PROJECT_ROOT${NC}"
echo ""

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print status
print_check() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$status" = "PASS" ]; then
        echo -e "  ${GREEN}✓${NC} $test_name ${GREEN}PASS${NC} $message"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    elif [ "$status" = "FAIL" ]; then
        echo -e "  ${RED}✗${NC} $test_name ${RED}FAIL${NC} $message"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    elif [ "$status" = "WARN" ]; then
        echo -e "  ${YELLOW}⚠${NC} $test_name ${YELLOW}WARN${NC} $message"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "  ${CYAN}ℹ${NC} $test_name ${CYAN}INFO${NC} $message"
    fi
}

print_section() {
    echo ""
    echo -e "${PURPLE}=== $1 ===${NC}"
}

# Check file existence
check_file() {
    local file_path="$1"
    local description="$2"

    if [ -f "$file_path" ]; then
        print_check "$description" "PASS" "Found: $file_path"
        return 0
    else
        print_check "$description" "FAIL" "Missing: $file_path"
        return 1
    fi
}

# Check directory existence
check_directory() {
    local dir_path="$1"
    local description="$2"

    if [ -d "$dir_path" ]; then
        print_check "$description" "PASS" "Found: $dir_path"
        return 0
    else
        print_check "$description" "FAIL" "Missing: $dir_path"
        return 1
    fi
}

# Check Python import
check_python_import() {
    local module="$1"
    local description="$2"

    if python3 -c "import $module" 2>/dev/null; then
        print_check "$description" "PASS" "Module '$module' can be imported"
        return 0
    else
        print_check "$description" "FAIL" "Module '$module' cannot be imported"
        return 1
    fi
}

# Check Node.js package
check_node_package() {
    local package_dir="$1"
    local description="$2"

    if [ -f "$package_dir/package.json" ]; then
        if [ -d "$package_dir/node_modules" ] || [ -f "$package_dir/package-lock.json" ]; then
            print_check "$description" "PASS" "Package ready: $package_dir"
            return 0
        else
            print_check "$description" "WARN" "Package.json found but dependencies not installed: $package_dir"
            return 1
        fi
    else
        print_check "$description" "FAIL" "No package.json found: $package_dir"
        return 1
    fi
}

print_section "PROJECT STRUCTURE CHECK"

# Check main directories
check_directory "$PROJECT_ROOT/ResortApp" "FastAPI Backend Directory"
check_directory "$PROJECT_ROOT/landingpage" "Landing Page Directory"
check_directory "$PROJECT_ROOT/dasboard" "Dashboard Directory"
check_directory "$PROJECT_ROOT/userend" "User End Directory"

# Check FastAPI structure
check_directory "$PROJECT_ROOT/ResortApp/app" "FastAPI App Directory"
check_directory "$PROJECT_ROOT/ResortApp/app/api" "API Routes Directory"
check_directory "$PROJECT_ROOT/ResortApp/app/models" "Models Directory"
check_directory "$PROJECT_ROOT/ResortApp/app/schemas" "Schemas Directory"
check_directory "$PROJECT_ROOT/ResortApp/app/curd" "CRUD Directory"
check_directory "$PROJECT_ROOT/ResortApp/app/utils" "Utils Directory"

print_section "CONFIGURATION FILES CHECK"

# Check configuration files
check_file "$PROJECT_ROOT/ResortApp/main.py" "FastAPI Main Application"
check_file "$PROJECT_ROOT/ResortApp/requirements_production.txt" "Production Requirements"
check_file "$PROJECT_ROOT/ResortApp/gunicorn.conf.py" "Gunicorn Configuration"
check_file "$PROJECT_ROOT/ResortApp/nginx.conf" "Nginx Configuration"
check_file "$PROJECT_ROOT/ResortApp/resort.service" "Systemd Service File"
check_file "$PROJECT_ROOT/ResortApp/deploy.sh" "Deployment Script"

# Check environment files
if [ -f "$PROJECT_ROOT/ResortApp/.env.production" ]; then
    print_check "Production Environment File" "PASS" "Found .env.production"
elif [ -f "$PROJECT_ROOT/ResortApp/.env" ]; then
    print_check "Environment File" "WARN" "Found .env (consider creating .env.production)"
else
    print_check "Environment File" "FAIL" "No environment file found"
fi

print_section "FRONTEND APPLICATIONS CHECK"

# Check landing page
check_file "$PROJECT_ROOT/landingpage/index.html" "Landing Page HTML"

# Check dashboard
check_node_package "$PROJECT_ROOT/dasboard" "Dashboard Package"
if [ -d "$PROJECT_ROOT/dasboard/build" ]; then
    print_check "Dashboard Build" "PASS" "Build directory exists"
    check_file "$PROJECT_ROOT/dasboard/build/index.html" "Dashboard Build HTML"
else
    print_check "Dashboard Build" "WARN" "Build directory missing (run 'npm run build')"
fi

# Check user end
if [ -d "$PROJECT_ROOT/userend/userend" ]; then
    check_node_package "$PROJECT_ROOT/userend/userend" "User End Package"
    if [ -d "$PROJECT_ROOT/userend/userend/build" ]; then
        print_check "User End Build" "PASS" "Build directory exists"
        check_file "$PROJECT_ROOT/userend/userend/build/index.html" "User End Build HTML"
    else
        print_check "User End Build" "WARN" "Build directory missing (run 'npm run build')"
    fi
else
    check_node_package "$PROJECT_ROOT/userend" "User End Package"
fi

print_section "PYTHON DEPENDENCIES CHECK"

# Change to FastAPI directory for Python checks
cd "$PROJECT_ROOT/ResortApp"

# Check if virtual environment exists
if [ -d "venv" ]; then
    print_check "Virtual Environment" "PASS" "venv directory found"

    # Activate virtual environment if available
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_check "Virtual Environment Activation" "PASS" "Activated successfully"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_check "Virtual Environment Activation" "PASS" "Activated successfully (Windows)"
    else
        print_check "Virtual Environment Activation" "WARN" "Activation script not found"
    fi
else
    print_check "Virtual Environment" "WARN" "No venv directory found"
fi

# Check critical Python imports
critical_modules=(
    "fastapi"
    "uvicorn"
    "sqlalchemy"
    "psycopg2"
    "bcrypt"
    "passlib"
    "python_jose"
    "pydantic"
    "python_dotenv"
)

for module in "${critical_modules[@]}"; do
    if [ "$module" = "python_jose" ]; then
        check_python_import "jose" "Python-JOSE Library"
    elif [ "$module" = "python_dotenv" ]; then
        check_python_import "dotenv" "Python-Dotenv Library"
    else
        check_python_import "$module" "$(echo $module | tr '_' ' ' | sed 's/\b\w/\U&/g') Library"
    fi
done

print_section "APPLICATION IMPORTS CHECK"

# Check FastAPI application imports
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print('SUCCESS: FastAPI app imported')
except ImportError as e:
    print(f'ERROR: Cannot import FastAPI app: {e}')
    sys.exit(1)
" 2>/dev/null; then
    print_check "FastAPI Application Import" "PASS" "Main app can be imported"
else
    print_check "FastAPI Application Import" "FAIL" "Cannot import main FastAPI app"
fi

# Check database connection
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.database import engine, Base
    print('SUCCESS: Database modules imported')
except ImportError as e:
    print(f'ERROR: Cannot import database modules: {e}')
    sys.exit(1)
" 2>/dev/null; then
    print_check "Database Modules Import" "PASS" "Database modules can be imported"
else
    print_check "Database Modules Import" "FAIL" "Cannot import database modules"
fi

# Check API modules
api_modules=(
    "auth"
    "user"
    "room"
    "packages"
    "frontend"
    "booking"
    "dashboard"
)

for module in "${api_modules[@]}"; do
    if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.api import $module
    print('SUCCESS')
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>/dev/null; then
        print_check "API Module: $module" "PASS" "Module can be imported"
    else
        print_check "API Module: $module" "FAIL" "Cannot import module"
    fi
done

print_section "SYSTEM REQUIREMENTS CHECK"

# Check system commands
system_commands=(
    "python3:Python 3"
    "pip3:Pip 3"
    "node:Node.js"
    "npm:NPM"
    "nginx:Nginx"
    "systemctl:Systemd"
    "curl:cURL"
    "git:Git"
)

for cmd_info in "${system_commands[@]}"; do
    IFS=':' read -r cmd desc <<< "$cmd_info"
    if command -v "$cmd" >/dev/null 2>&1; then
        version=$($cmd --version 2>/dev/null | head -n1 || echo "Unknown version")
        print_check "$desc Availability" "PASS" "$version"
    else
        print_check "$desc Availability" "FAIL" "Command not found: $cmd"
    fi
done

print_section "DEPLOYMENT READINESS CHECK"

# Check deployment script permissions
if [ -f "$PROJECT_ROOT/ResortApp/deploy.sh" ]; then
    if [ -x "$PROJECT_ROOT/ResortApp/deploy.sh" ]; then
        print_check "Deployment Script Permissions" "PASS" "deploy.sh is executable"
    else
        print_check "Deployment Script Permissions" "WARN" "deploy.sh not executable (run: chmod +x deploy.sh)"
    fi
fi

# Check for sensitive information
if grep -r "password.*=" "$PROJECT_ROOT/ResortApp" --include="*.py" --include="*.js" --exclude="*.example" 2>/dev/null | grep -v "password_hash" | grep -v "get_password" | grep -v "verify_password" >/dev/null; then
    print_check "Hardcoded Passwords Check" "WARN" "Potential hardcoded passwords found - review code"
else
    print_check "Hardcoded Passwords Check" "PASS" "No hardcoded passwords detected"
fi

# Check for API keys
if grep -r "api_key\|secret_key\|private_key" "$PROJECT_ROOT/ResortApp" --include="*.py" --include="*.js" --exclude="*.example" 2>/dev/null | grep -v "SECRET_KEY.*os.getenv" >/dev/null; then
    print_check "Hardcoded API Keys Check" "WARN" "Potential hardcoded API keys found - review code"
else
    print_check "Hardcoded API Keys Check" "PASS" "No hardcoded API keys detected"
fi

print_section "DOCKER CONFIGURATION CHECK (OPTIONAL)"

if [ -f "$PROJECT_ROOT/ResortApp/Dockerfile" ]; then
    print_check "Dockerfile" "PASS" "Dockerfile found"

    if [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/ResortApp/docker-compose.yml" ]; then
        print_check "Docker Compose" "PASS" "docker-compose.yml found"
    else
        print_check "Docker Compose" "INFO" "docker-compose.yml not found (optional)"
    fi
else
    print_check "Docker Configuration" "INFO" "No Docker configuration found (deployment script will handle setup)"
fi

print_section "SECURITY CHECKLIST"

# Basic security checks
security_files=(
    ".gitignore:Git ignore file"
    ".env.example:Environment example file"
)

for file_info in "${security_files[@]}"; do
    IFS=':' read -r file desc <<< "$file_info"
    if [ -f "$PROJECT_ROOT/ResortApp/$file" ]; then
        print_check "$desc" "PASS" "File exists"
    else
        print_check "$desc" "INFO" "File not found (recommended)"
    fi
done

print_section "FINAL SUMMARY"

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                    VERIFICATION RESULTS                        ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! Your application is ready for deployment.${NC}"
    echo ""
    echo -e "${GREEN}Total Checks: $TOTAL_CHECKS${NC}"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${GREEN}Failed: $FAILED_CHECKS${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "1. Upload your project to the server"
    echo -e "2. Run the deployment script: ${YELLOW}sudo ./deploy.sh${NC}"
    echo -e "3. Follow the post-deployment checklist"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED! Please fix the issues before deployment.${NC}"
    echo ""
    echo -e "${RED}Total Checks: $TOTAL_CHECKS${NC}"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""
    echo -e "${YELLOW}Common Fixes:${NC}"
    echo -e "1. Install missing Python packages: ${YELLOW}pip install -r requirements_production.txt${NC}"
    echo -e "2. Build React applications: ${YELLOW}npm run build${NC} in dashboard and userend directories"
    echo -e "3. Create environment file: ${YELLOW}cp .env.example .env.production${NC}"
    echo -e "4. Make deploy script executable: ${YELLOW}chmod +x deploy.sh${NC}"
    echo ""
    exit 1
fi
