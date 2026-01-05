#!/usr/bin/env bash
#
# Test suite for termwall
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERMWALL="$SCRIPT_DIR/termwall"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++)) || true
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++)) || true
}

# ==============================================================================
# Tests
# ==============================================================================

echo "Running termwall tests..."
echo ""

# Test: Help command
if "$TERMWALL" help > /dev/null 2>&1; then
    pass "help command works"
else
    fail "help command failed"
fi

# Test: Version command
if "$TERMWALL" version | grep -q "termwall version"; then
    pass "version command works"
else
    fail "version command failed"
fi

# Test: List modes
if "$TERMWALL" list-modes | grep -q "stars"; then
    pass "list-modes includes stars"
else
    fail "list-modes missing stars"
fi

if "$TERMWALL" list-modes | grep -q "bounce"; then
    pass "list-modes includes bounce"
else
    fail "list-modes missing bounce"
fi

if "$TERMWALL" list-modes | grep -q "matrix"; then
    pass "list-modes includes matrix"
else
    fail "list-modes missing matrix"
fi

# Test: Validate config (example file)
if "$TERMWALL" validate-config --config "$SCRIPT_DIR/config.example" | grep -q "valid"; then
    pass "validate-config accepts example config"
else
    fail "validate-config rejects example config"
fi

# Test: Validate config (invalid mode)
TEMP_CONFIG=$(mktemp)
echo "mode = invalid_mode" > "$TEMP_CONFIG"
if ! "$TERMWALL" validate-config --config "$TEMP_CONFIG" >/dev/null 2>&1; then
    pass "validate-config rejects invalid mode"
else
    fail "validate-config accepts invalid mode"
fi
rm -f "$TEMP_CONFIG"

# Test: Validate config (invalid fps)
TEMP_CONFIG=$(mktemp)
echo "fps = 999" > "$TEMP_CONFIG"
if ! "$TERMWALL" validate-config --config "$TEMP_CONFIG" >/dev/null 2>&1; then
    pass "validate-config rejects invalid fps"
else
    fail "validate-config accepts invalid fps"
fi
rm -f "$TEMP_CONFIG"

# Test: Validate config (invalid color theme)
TEMP_CONFIG=$(mktemp)
echo "color_theme = rainbow" > "$TEMP_CONFIG"
if ! "$TERMWALL" validate-config --config "$TEMP_CONFIG" >/dev/null 2>&1; then
    pass "validate-config rejects invalid color_theme"
else
    fail "validate-config accepts invalid color_theme"
fi
rm -f "$TEMP_CONFIG"

# Test: Smoke test (requires real PTY, skip in VS Code)
echo ""
if [[ -n "${VSCODE_INJECTION:-}" ]] || [[ -n "${VSCODE_GIT_IPC_HANDLE:-}" ]] || [[ "$TERM_PROGRAM" == "vscode" ]]; then
    echo "Skipping smoke tests (VS Code terminal detected)"
    echo "Run these tests in a real terminal for full coverage"
else
    echo "Running smoke tests (require pseudo-terminal)..."
    
    for mode in stars bounce matrix; do
        if script -q -c "$TERMWALL run --mode $mode --duration 1" /dev/null 2>/dev/null; then
            pass "smoke test: $mode mode runs and exits cleanly"
        else
            fail "smoke test: $mode mode failed"
        fi
    done
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "=========================================="
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo "=========================================="

if [[ "$TESTS_FAILED" -gt 0 ]]; then
    exit 1
fi

exit 0
