#!/bin/bash
set -euo pipefail

# Usage: .github/scripts/fetch_findings.sh [branch-name]
# If no branch is provided, uses the current git branch.
# Requires: gh CLI authenticated with repo access.

BRANCH="${1:-$(git branch --show-current)}"
REPO="${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

echo "Fetching latest security findings for branch: $BRANCH"

# Find the latest completed security-scan workflow run for this branch
RUN_ID=$(gh api \
  "/repos/$REPO/actions/workflows/security-scan.yml/runs?branch=$BRANCH&status=completed&per_page=1" \
  --jq '.workflow_runs[0].id // empty')

if [ -z "$RUN_ID" ]; then
  echo "No completed security scan found for branch '$BRANCH'."
  echo "The scan may not have run yet, or the branch name may be incorrect."
  exit 1
fi

RUN_DATE=$(gh api \
  "/repos/$REPO/actions/runs/$RUN_ID" \
  --jq '.updated_at // "unknown"')

echo "Found scan run $RUN_ID (completed: $RUN_DATE)"

# Create output directory
mkdir -p .security

# Download the findings artifact
gh run download "$RUN_ID" \
  --name security-findings \
  --dir .security 2>/dev/null \
  || { echo "Could not download security-findings artifact from run $RUN_ID."; exit 1; }

# Also download the state file for reference
gh run download "$RUN_ID" \
  --name security-findings-state \
  --dir .security 2>/dev/null \
  || echo "Note: state file not available (first run or expired)."

echo ""
echo "Findings downloaded to .security/SECURITY_FINDINGS.md"
echo "Scan run:   $RUN_ID"
echo "Completed:  $RUN_DATE"
echo "Branch:     $BRANCH"
echo ""

# Print summary
if [ -f .security/SECURITY_FINDINGS.md ]; then
  OPEN=$(grep -c '\*\*Status:\*\* OPEN' .security/SECURITY_FINDINGS.md 2>/dev/null || echo "0")
  BLOCKING=$(grep -c '\*\*Blocking:\*\* YES' .security/SECURITY_FINDINGS.md 2>/dev/null || echo "0")
  echo "Summary: $OPEN open findings, $BLOCKING blocking"
fi