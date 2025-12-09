#!/bin/bash
# ============================================================================
# Liquid Zimbabwe 4G Network Optimizer - Docker Deployment Test
# Purpose: Validate Phase 5 Docker deployment with updated tools
# Created: 2025-11-03
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Print functions
print_header() {
    echo -e "\n${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}\n"
}

print_test() {
    local name="$1"
    local status="$2"
    local details="$3"

    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✓${NC} $name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $name"
        ((TESTS_FAILED++))
    fi

    if [ -n "$details" ]; then
        echo -e "   $details"
    fi
}

print_summary() {
    local total=$((TESTS_PASSED + TESTS_FAILED))
    echo -e "\n${BOLD}Test Summary:${NC}"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}/$total"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}/$total"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}✅ ALL TESTS PASSED - DOCKER DEPLOYMENT READY${NC}"
        return 0
    else
        echo -e "\n${YELLOW}${BOLD}⚠ SOME TESTS FAILED - REVIEW ERRORS ABOVE${NC}"
        return 1
    fi
}

# ============================================================================
# Test 1: Check Docker availability
# ============================================================================
test_docker_installed() {
    print_header "Test 1: Docker Installation"

    if command -v docker &> /dev/null; then
        local version=$(docker --version)
        print_test "Docker installed" "pass" "$version"
        return 0
    else
        print_test "Docker installed" "fail" "Docker not found in PATH"
        return 1
    fi
}

# ============================================================================
# Test 2: Build Docker image
# ============================================================================
test_docker_build() {
    print_header "Test 2: Docker Image Build"

    echo "Building Docker image: lz-network-optimizer:phase5"
    echo "This may take several minutes..."

    if docker build -f docker/Dockerfile -t lz-network-optimizer:phase5 . > /tmp/docker_build.log 2>&1; then
        local image_size=$(docker images lz-network-optimizer:phase5 --format "{{.Size}}")
        print_test "Docker build successful" "pass" "Image size: $image_size"
        return 0
    else
        print_test "Docker build" "fail" "See /tmp/docker_build.log for details"
        tail -20 /tmp/docker_build.log
        return 1
    fi
}

# ============================================================================
# Test 3: Verify image contains updated tools
# ============================================================================
test_updated_tools_present() {
    print_header "Test 3: Updated Tools Verification"

    # Check if rollback_manager.py exists in image
    if docker run --rm lz-network-optimizer:phase5 ls /app/tools/rollback_manager.py > /dev/null 2>&1; then
        print_test "rollback_manager.py present" "pass"
    else
        print_test "rollback_manager.py present" "fail"
        return 1
    fi

    # Check if updated huawei_tools.py contains new function
    if docker run --rm lz-network-optimizer:phase5 grep -q "modify_huawei_parameter_site" /app/tools/huawei_tools.py; then
        print_test "modify_huawei_parameter_site tool present" "pass"
    else
        print_test "modify_huawei_parameter_site tool present" "fail"
        return 1
    fi

    # Check if backup exists
    if docker run --rm lz-network-optimizer:phase5 ls /app/tools/huawei_tools_original.py > /dev/null 2>&1; then
        print_test "Original tools backup present" "pass"
    else
        print_test "Original tools backup present" "fail"
    fi

    return 0
}

# ============================================================================
# Test 4: Test tool imports in container
# ============================================================================
test_tool_imports_container() {
    print_header "Test 4: Tool Imports in Container"

    # Test Python import of updated tools
    if docker run --rm lz-network-optimizer:phase5 python3 -c "from tools.huawei_tools import HUAWEI_TOOLS; print(f'{len(HUAWEI_TOOLS)} tools loaded')" 2>&1 | grep -q "6 tools loaded"; then
        print_test "Huawei tools import" "pass" "6 tools loaded"
    else
        print_test "Huawei tools import" "fail"
        return 1
    fi

    # Test rollback manager import
    if docker run --rm lz-network-optimizer:phase5 python3 -c "from tools.rollback_manager import ROLLBACK_TOOLS; print(f'{len(ROLLBACK_TOOLS)} rollback tools loaded')" 2>&1 | grep -q "4 rollback tools loaded"; then
        print_test "Rollback manager import" "pass" "4 rollback tools loaded"
    else
        print_test "Rollback manager import" "fail"
        return 1
    fi

    return 0
}

# ============================================================================
# Test 5: Test database loading
# ============================================================================
test_database_loading() {
    print_header "Test 5: Database Loading"

    # Check if database file exists
    if docker run --rm -v "$(pwd)/data:/app/data" lz-network-optimizer:phase5 ls /app/data/lz_network.db > /dev/null 2>&1; then
        print_test "Database file present" "pass"
    else
        print_test "Database file present" "fail"
        return 1
    fi

    # Test database connectivity
    if docker run --rm -v "$(pwd)/data:/app/data" lz-network-optimizer:phase5 python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/lz_network.db'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM sites'); print(f'{cur.fetchone()[0]} sites'); conn.close()" 2>&1 | grep -q "sites"; then
        local site_count=$(docker run --rm -v "$(pwd)/data:/app/data" lz-network-optimizer:phase5 python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/lz_network.db'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM sites'); print(cur.fetchone()[0]); conn.close()" 2>&1)
        print_test "Database connectivity" "pass" "$site_count sites in database"
    else
        print_test "Database connectivity" "fail"
        return 1
    fi

    return 0
}

# ============================================================================
# Test 6: Test API connectivity from container
# ============================================================================
test_api_connectivity_container() {
    print_header "Test 6: API Connectivity from Container"

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_test "Environment file present" "fail" ".env file not found"
        return 1
    fi

    print_test "Environment file present" "pass"

    # Run API connectivity test in container
    echo "Testing API connectivity from container..."
    if docker run --rm --env-file .env -v "$(pwd)/data:/app/data" lz-network-optimizer:phase5 python3 test_updated_tools.py 2>&1 | grep -q "API Connectivity"; then
        print_test "API connectivity test executed" "pass"
    else
        print_test "API connectivity test executed" "fail"
        return 1
    fi

    return 0
}

# ============================================================================
# Test 7: Test UI startup
# ============================================================================
test_ui_startup() {
    print_header "Test 7: UI Startup Test"

    echo "Starting UI container in background..."

    # Start container with UI
    docker run -d --name lz-ui-test --env-file .env -v "$(pwd)/data:/app/data" -p 8501:8501 lz-network-optimizer:phase5 streamlit run ui/app.py --server.headless=true > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        print_test "UI container started" "pass"

        # Wait for UI to start
        echo "Waiting for UI to start (10 seconds)..."
        sleep 10

        # Check if UI is responding
        if docker logs lz-ui-test 2>&1 | grep -q "You can now view your Streamlit app"; then
            print_test "UI started successfully" "pass" "Streamlit running on port 8501"
        else
            print_test "UI started successfully" "fail"
            docker logs lz-ui-test 2>&1 | tail -20
        fi

        # Cleanup
        docker stop lz-ui-test > /dev/null 2>&1
        docker rm lz-ui-test > /dev/null 2>&1
    else
        print_test "UI container started" "fail"
        return 1
    fi

    return 0
}

# ============================================================================
# Test 8: Test docker-compose
# ============================================================================
test_docker_compose() {
    print_header "Test 8: Docker Compose Validation"

    if command -v docker-compose &> /dev/null; then
        print_test "docker-compose installed" "pass"
    else
        print_test "docker-compose installed" "fail" "docker-compose not found"
        return 1
    fi

    # Validate docker-compose.yml
    if docker-compose -f docker/docker-compose.yml config > /dev/null 2>&1; then
        print_test "docker-compose.yml valid" "pass"
    else
        print_test "docker-compose.yml valid" "fail"
        return 1
    fi

    # Test docker-compose build
    echo "Building with docker-compose..."
    if docker-compose -f docker/docker-compose.yml build > /tmp/compose_build.log 2>&1; then
        print_test "docker-compose build successful" "pass"
    else
        print_test "docker-compose build successful" "fail"
        tail -20 /tmp/compose_build.log
        return 1
    fi

    return 0
}

# ============================================================================
# Main execution
# ============================================================================
main() {
    echo -e "${BOLD}LIQUID ZIMBABWE 4G NETWORK OPTIMIZER${NC}"
    echo -e "${BOLD}Phase 5 - Docker Deployment Test Suite${NC}"
    echo -e "${BOLD}========================================${NC}"

    # Navigate to project root
    cd "$(dirname "$0")"

    # Run tests
    test_docker_installed || exit 1
    test_docker_build || exit 1
    test_updated_tools_present
    test_tool_imports_container
    test_database_loading
    test_api_connectivity_container
    test_ui_startup
    test_docker_compose

    # Print summary
    print_summary
    exit $?
}

# Run main function
main
