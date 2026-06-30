#!/usr/bin/env bash
# init.sh — Environment verification and initialization
#
# This script is run by the agent at the START of a session and before
# declaring any task as `done`. If it fails, the session must not proceed.
#
# Expected output: clear exit codes and blocks marked with [OK]/[FAIL].
#
# Behavior:
#   - Steps 1-3: Harness base files (always checked, fail if missing)
#   - Steps 4-7: Docker build/test (skipped with [WARN] if Docker or
#     docker-compose.yml are missing — expected during bootstrap feature 0)

set -u
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

EXIT_CODE=0
SKIP_DOCKER=0

echo "── 1. Checking environment ─────────────────────────────"

# Docker available
if ! command -v docker >/dev/null 2>&1; then
  warn "docker is not installed (expected during bootstrap)"
  SKIP_DOCKER=1
else
  ok "docker -> $(docker --version | head -1)"
fi

# Docker Compose available
if [ "$SKIP_DOCKER" -eq 0 ]; then
  if ! docker compose version >/dev/null 2>&1; then
    warn "docker compose is not available (expected during bootstrap)"
    SKIP_DOCKER=1
  else
    ok "docker compose available"
  fi
fi

# Docker daemon running
if [ "$SKIP_DOCKER" -eq 0 ]; then
  if ! docker info >/dev/null 2>&1; then
    warn "Docker daemon is not running (expected during bootstrap)"
    SKIP_DOCKER=1
  else
    ok "Docker daemon is running"
  fi
fi

# Python available (for local scripts / validation)
if command -v python3 >/dev/null 2>&1; then
  ok "python3 -> $(python3 --version)"
else
  warn "python3 not found (only needed for local scripts)"
fi

echo ""
echo "── 2. Checking harness base files ──────────────────────"

for f in AGENTS.md feature_list.json progress/current.md docs/architecture.md docs/conventions.md docs/verification.md docs/domain.md docs/tech-stack.md CHECKPOINTS.md; do
  if [ ! -f "$f" ]; then
    fail "Missing base file: $f"
    EXIT_CODE=1
  else
    ok "Exists $f"
  fi
done

# .env.example is optional during bootstrap (feature 0 creates it)
if [ ! -f ".env.example" ]; then
  warn "Missing .env.example (will be created by bootstrap feature)"
else
  ok "Exists .env.example"
fi

echo ""
echo "── 3. Validating feature_list.json ──────────────────────"

if [ -f "feature_list.json" ]; then
  python3 - <<'PY'
import json, sys
try:
    data = json.load(open("feature_list.json"))
    valid = {"pending", "in_progress", "done", "blocked"}
    in_progress = [f for f in data["features"] if f["status"] == "in_progress"]
    if len(in_progress) > 1:
        print(f"[FAIL]  {len(in_progress)} features in in_progress (max 1)")
        sys.exit(1)
    for f in data["features"]:
        if f["status"] not in valid:
            print(f"[FAIL]  Invalid status on feature {f['id']}: {f['status']}")
            sys.exit(1)
        if "acceptance" not in f or not isinstance(f["acceptance"], list):
            print(f"[FAIL]  Feature {f['id']} missing 'acceptance' list")
            sys.exit(1)
    print(f"[OK]    feature_list.json valid ({len(data['features'])} features)")
except Exception as e:
    print(f"[FAIL]  feature_list.json invalid: {e}")
    sys.exit(1)
PY
  if [ $? -ne 0 ]; then EXIT_CODE=1; fi
else
  fail "feature_list.json not found"
  EXIT_CODE=1
fi

# Skip Docker steps if Docker is not available or docker-compose.yml missing
if [ "$SKIP_DOCKER" -eq 1 ]; then
  echo ""
  echo "── 4-7. Skipping Docker steps (no Docker available) ────"
  warn "Docker not available — skipping container build, service wait, and tests"
  warn "This is expected during bootstrap (feature 0). Run init.sh again after feature 0 completes."
  echo ""
  echo "── Summary ─────────────────────────────────────────────"
  if [ "$EXIT_CODE" -eq 0 ]; then
    ok "Harness files OK. Docker steps skipped (bootstrap mode)."
  else
    fail "Harness files have errors. Fix them before proceeding."
  fi
  exit $EXIT_CODE
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
  echo ""
  echo "── 4-7. Skipping Docker steps (no docker-compose.yml) ──"
  warn "docker-compose.yml not found — skipping container build, service wait, and tests"
  warn "This is expected during bootstrap (feature 0). Run init.sh again after feature 0 completes."
  echo ""
  echo "── Summary ─────────────────────────────────────────────"
  if [ "$EXIT_CODE" -eq 0 ]; then
    ok "Harness files OK. Docker steps skipped (bootstrap mode)."
  else
    fail "Harness files have errors. Fix them before proceeding."
  fi
  exit $EXIT_CODE
fi

echo ""
echo "── 4. Building and starting containers ─────────────────"

if docker compose up --build -d 2>&1; then
  ok "Containers built and started"
else
  fail "docker compose up --build failed"
  EXIT_CODE=1
fi

echo ""
echo "── 5. Waiting for services ─────────────────────────────"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
for i in {1..15}; do
  if docker compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
    ok "PostgreSQL is ready"
    break
  fi
  if [ "$i" -eq 15 ]; then
    fail "PostgreSQL did not become ready in time"
    EXIT_CODE=1
  fi
  sleep 2
done

# Wait for app
echo "Waiting for app..."
for i in {1..15}; do
  if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
    ok "App is running at http://localhost:8000"
    break
  fi
  if [ "$i" -eq 15 ]; then
    fail "App did not become ready in time"
    EXIT_CODE=1
  fi
  sleep 2
done

echo ""
echo "── 6. Running tests ────────────────────────────────────"

TEST_OUTPUT=$(docker compose exec -T app pytest backend/tests/ -v --tb=short 2>&1)
TEST_EXIT=$?

if [ $TEST_EXIT -eq 0 ]; then
  ok "All tests pass"
elif [ $TEST_EXIT -eq 5 ] && echo "$TEST_OUTPUT" | grep -q "no tests ran"; then
  warn "No tests found (expected in early features)"
else
  fail "Some tests failed"
  echo "$TEST_OUTPUT"
  EXIT_CODE=1
fi

echo ""
echo "── 7. Summary ─────────────────────────────────────────"

if [ $EXIT_CODE -eq 0 ]; then
  ok "Environment ready. You can start working."
else
  fail "Environment NOT ready. Fix the errors before proceeding."
fi

exit $EXIT_CODE
