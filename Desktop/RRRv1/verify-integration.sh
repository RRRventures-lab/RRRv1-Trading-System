#!/bin/bash

# ============================================================================
# RRRv1 INTEGRATION VERIFICATION SCRIPT
# ============================================================================
# This script verifies that all components of the RRRv1 trading system
# are properly configured and ready for deployment
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================================
# START VERIFICATION
# ============================================================================

print_header "RRRv1 INTEGRATION VERIFICATION"

# Check 1: Frontend Build
print_header "FRONTEND BUILD VERIFICATION"

if [ -f "frontend/dist/index.html" ]; then
    check_pass "Frontend dist/index.html exists"
else
    check_fail "Frontend dist/index.html missing"
fi

if [ -f "frontend/dist/assets/index-"*.js ]; then
    check_pass "Frontend JavaScript bundle exists"
else
    check_fail "Frontend JavaScript bundle missing"
fi

if [ -f "frontend/dist/assets/index-"*.css ]; then
    check_pass "Frontend CSS bundle exists"
else
    check_fail "Frontend CSS bundle missing"
fi

if [ -f "frontend/package.json" ]; then
    check_pass "Frontend package.json exists"
else
    check_fail "Frontend package.json missing"
fi

# Check 2: Backend Files
print_header "BACKEND FILES VERIFICATION"

if [ -f "backend/api_server.py" ]; then
    check_pass "Backend api_server.py exists"
else
    check_fail "Backend api_server.py missing"
fi

if [ -f "backend/models.py" ]; then
    check_pass "Backend models.py exists"
else
    check_fail "Backend models.py missing"
fi

if [ -f "backend/database.py" ]; then
    check_pass "Backend database.py exists"
else
    check_fail "Backend database.py missing"
fi

if [ -f "backend/agent_integration.py" ]; then
    check_pass "Backend agent_integration.py exists"
else
    check_fail "Backend agent_integration.py missing"
fi

# Check 3: Trading System Files
print_header "TRADING SYSTEM FILES VERIFICATION"

if [ -d "src/agents" ]; then
    check_pass "Trading agents directory exists"
else
    check_fail "Trading agents directory missing"
fi

if [ -d "src/strategies" ]; then
    check_pass "Strategies directory exists"
else
    check_fail "Strategies directory missing"
fi

if [ -d "src/execution" ]; then
    check_pass "Execution directory exists"
else
    check_fail "Execution directory missing"
fi

if [ -d "src/risk" ]; then
    check_pass "Risk management directory exists"
else
    check_fail "Risk management directory missing"
fi

# Check 4: Documentation
print_header "DOCUMENTATION VERIFICATION"

if [ -f "docs/FRONTEND_BUILD_GUIDE.md" ]; then
    check_pass "Frontend Build Guide exists"
else
    check_fail "Frontend Build Guide missing"
fi

if [ -f "docs/COMPLETE_SYSTEM_GUIDE.md" ]; then
    check_pass "Complete System Guide exists"
else
    check_fail "Complete System Guide missing"
fi

if [ -f "SYSTEM_READY.txt" ]; then
    check_pass "System Ready summary exists"
else
    check_fail "System Ready summary missing"
fi

# Check 5: Configuration Files
print_header "CONFIGURATION FILES VERIFICATION"

if [ -f "frontend/vite.config.ts" ]; then
    check_pass "Vite configuration exists"
else
    check_fail "Vite configuration missing"
fi

if [ -f "frontend/tailwind.config.js" ]; then
    check_pass "Tailwind configuration exists"
else
    check_fail "Tailwind configuration missing"
fi

if [ -f ".env.example" ]; then
    check_pass "Environment variables template exists"
else
    check_fail "Environment variables template missing"
fi

# Check 6: Node Dependencies
print_header "NODE DEPENDENCIES VERIFICATION"

if [ -d "frontend/node_modules" ]; then
    check_pass "Node modules installed"
else
    check_warn "Node modules not installed (run 'npm install' in frontend/)"
fi

# Check 7: TypeScript Compilation
print_header "TYPESCRIPT COMPILATION CHECK"

cd frontend
if npm run type-check &>/dev/null; then
    check_pass "TypeScript compilation clean"
    cd ..
else
    check_fail "TypeScript compilation has errors"
    cd ..
fi

# Summary
print_header "VERIFICATION SUMMARY"

echo "Checks Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo "Checks Failed: ${RED}$CHECKS_FAILED${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL CHECKS PASSED - System is ready for deployment!${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ $CHECKS_FAILED checks failed - Please review and fix issues above${NC}\n"
    exit 1
fi
