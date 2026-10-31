#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/.."
for file in scripts/*.sh; do bash -n "$file"; done
shellcheck scripts/*.sh
bash scripts/ci-template.test.sh
bash scripts/setup-repo.test.sh
bash scripts/sync-agent-standards.test.sh
node scripts/sync-llms.test.cjs
node --test scripts/organization.test.cjs scripts/check-library.test.cjs scripts/sync-repo.test.cjs scripts/delivery.test.cjs templates/actions/verification/verification.test.cjs
node templates/llms/build-llms-core.test.js
