#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-only
#
# CI-friendly doorstop validation wrapper.
#
# Runs `doorstop` with flags that escalate WARNING to ERROR, so any real issue
# fails the build. Accepts extra args that are passed through to doorstop (so
# callers can e.g. `doorstop_lint.sh -s LEGACY` to skip one document).
#
# Default behavior:
#   -e   escalate WARNING -> ERROR (non-zero exit)
#   -Z   strict-child-check: every parent item must be referenced downstream
#
# Examples:
#   ./doorstop_lint.sh                       # default gate
#   ./doorstop_lint.sh -s LEGACY             # skip the LEGACY document
#   ./doorstop_lint.sh -R                    # also skip ref-file checks
#
# Set DOORSTOP_LINT_NO_STRICT=1 to drop -Z if your tree isn't ready for it.

set -euo pipefail

args=(-e)

if [[ "${DOORSTOP_LINT_NO_STRICT:-0}" != "1" ]]; then
  args+=(-Z)
fi

exec doorstop "${args[@]}" "$@"
