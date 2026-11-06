# Validation

Running `doorstop` (no subcommand) builds the tree, loads every document, and
validates every item. This reference covers the severity matrix, what each
global flag does, how suspect links work, and when skipping a check is safe
vs. sweeping a real problem under the rug.

## Severity matrix

| Level | Condition | Source of truth |
|---|---|---|
| INFO | Skipped levels within a document (e.g. `1.1` → `1.3`). | `docs/cli/validation.md:26` |
| INFO | No initial review done for an item (`reviewed: null`). | `docs/cli/validation.md:27` |
| INFO | UID prefix doesn't match document prefix (renamed document). | `docs/cli/validation.md:28` |
| INFO | Link UID prefix doesn't match target document's prefix. | `docs/cli/validation.md:29` |
| WARNING | Document contains no items. | `docs/cli/validation.md:33` |
| WARNING | Duplicate levels within a document. | `docs/cli/validation.md:34` |
| WARNING | Item has empty `text:`. | `docs/cli/validation.md:35` |
| WARNING | Item has unreviewed changes (current fingerprint ≠ `reviewed:`). | `docs/cli/validation.md:36` |
| WARNING | Child link references an **inactive** item. | `docs/cli/validation.md:37` |
| WARNING | Item is linked to a non-normative item (heading). | `docs/cli/validation.md:38` |
| WARNING | Item linked to itself. | `docs/cli/validation.md:39` |
| WARNING | Suspect link: stored parent-fingerprint ≠ parent's current fingerprint. | `docs/cli/validation.md:40` |
| WARNING | `-Z/--strict-child-check`: item in a parent doc has no child links. | `docs/cli/validation.md:42` |
| WARNING | Normative, non-derived item in a child doc has no parent links. | `docs/cli/validation.md:43` |
| WARNING | Non-normative item has links. | `docs/cli/validation.md:44` |
| WARNING | Cycle of item links (DFS detected by `CycleTracker`). | `docs/cli/validation.md:45` |
| ERROR | Parent link points to an **inactive** item. | `docs/cli/validation.md:49` |
| ERROR | Link UID is invalid or unknown. | `docs/cli/validation.md:50` |
| ERROR | `references:` / `ref:` cannot be resolved (file or keyword not found). | `docs/cli/validation.md:51` |

## Global validation flags

All of these apply to the bare `doorstop` command (the implicit "validate"
subcommand). They are parsed at the top level in
`doorstop/cli/main.py:83-149`.

| Flag | Effect | When to use |
|---|---|---|
| `-F`, `--no-reformat` | Don't rewrite item files in canonical YAML during validation. | You want to inspect exactly what's on disk without side effects. CI where writes would dirty the tree. |
| `-r`, `--reorder` | Re-pack document levels to remove gaps. Writes to disk. | After bulk deletes, when levels are full of gaps. |
| `-L`, `--no-level-check` | Skip level checks (skipped/duplicate/gaps). | Temporarily acceptable during bulk edits. Don't ship with this on. |
| `-R`, `--no-ref-check` | Skip `references:` / `ref:` file-existence checks. | Running outside the source checkout where referenced files live. |
| `-C`, `--no-child-check` | Skip child/reverse link checks. | When working on a single leaf document in isolation. |
| `-Z`, `--strict-child-check` | Require child links from every parent item. | Enforces fully-linked coverage. Use in CI for safety-critical trees. |
| `-S`, `--no-suspect-check` | Don't flag suspect links. | Never OK long-term. Sometimes useful during a planned cascade review. |
| `-W`, `--no-review-check` | Don't flag unreviewed items. | During bulk import, before the initial review pass. |
| `-s PREFIX`, `--skip PREFIX` | Exclude one document from validation. Repeatable. | The document is known broken and quarantined. |
| `-w`, `--warn-all` | Promote INFO → WARNING. | Pre-release sweeps. |
| `-e`, `--error-all` | Promote WARNING → ERROR (non-zero exit). | CI gate. See `scripts/doorstop_lint.sh`. |

Exit codes:

- `0` — no issues at or above the effective threshold.
- `1` — any issue at or above the effective threshold, or any uncaught
  `DoorstopError`/`DoorstopFileError`.

## Fingerprint and suspect links

Every item has a **current fingerprint** — SHA-256 (URL-safe Base64) of:

1. `uid`
2. `text`
3. `ref`
4. `references`
5. UIDs in `links`
6. Values of extended attrs listed in `attributes.reviewed`

When you run `doorstop review <UID>`, doorstop writes the current fingerprint
into the item's `reviewed:` field **and** copies the fingerprint of each
parent into the child's `links:` entry for that parent.

Later, when something changes:

- Item's current fingerprint drifts from its stored `reviewed:` → **unreviewed
  change** warning.
- Parent's current fingerprint drifts from the stamp in a child's `links:`
  entry → **suspect link** warning on the child.

A change to a parent **does not** automatically bump the parent's `reviewed:`
stamp. It bumps only when the parent itself is re-`review`ed. So the usual
churn flow is:

1. Edit parent `text`. → parent is unreviewed, children have suspect links.
2. `doorstop review <parent>` → parent is reviewed. Children still suspect
   (the new parent fingerprint ≠ child's stored parent-stamp).
3. On each child: either `doorstop clear <child>` (accept parent change
   without revisiting child text) or edit the child and `doorstop review
   <child>` (acknowledge parent change *and* update child content).

`clear` ≠ `review`. `clear` updates only the stored parent-stamps in the
child's `links:`. `review` updates the child's own `reviewed:` stamp (and
also refreshes link stamps as a side effect).

## Unresolved references

An item with `ref:` or `references:` that cannot be found on disk (or whose
keyword can't be grep'd from any text file) is an ERROR. To quiet this for a
specific run:

- `-R/--no-ref-check` — skip the check for the whole run.
- `doorstop -s <PREFIX>` — skip the offending document entirely.

Don't paper over this in `.doorstop.yml` — fix the path, remove the
reference, or park the document in `-s` until it's fixed.

## Cycle detection

Implemented in `commands.CycleTracker` (DFS). A cycle is reported once per
cycle as WARNING, with the cycle path rendered as `A → B → C → A`. Resolve by
`doorstop unlink <child> <parent>` on one of the edges.

## Levels: skipped, duplicate, gaps

- **Skipped**: `1.1` directly followed by `1.3`. INFO. Harmless but usually
  indicates a deleted sibling — consider `doorstop -r` to re-pack.
- **Duplicate**: two items share a level. WARNING. Fix with `doorstop edit
  <uid>` to assign a unique level, or `doorstop reorder <prefix>` to let
  doorstop resolve it interactively.
- **Headings**: `X.0` + `normative: false` is a heading. Headings do **not**
  count as duplicates of other headings in the same document.

## Strict-child-check

`-Z/--strict-child-check` enforces: every parent item must be referenced
(have a child link) from every child document. I.e. coverage must be
complete in both directions. Use this as a CI gate once the tree is mature.

## Warning-to-error promotion

`-e/--error-all` escalates every WARNING (and INFO, if also `-w`) to ERROR.
Combined with `-W` to tolerate unreviewed items while still hard-failing on
suspect links or cycles, this gives a tunable CI gate. See
`scripts/doorstop_lint.sh` for the canonical recipe.

## When skipping is safe

| Flag | Safe to skip *temporarily* | Safe to skip *permanently* |
|---|---|---|
| `-L` no-level-check | During bulk restructure | Rarely — level coherence matters for publishing |
| `-R` no-ref-check | Running outside source checkout | For docs with no external refs, it's harmless |
| `-C` no-child-check | Working on a single leaf doc | No — coverage should matter |
| `-S` no-suspect-check | Planned cascade review in flight | **Never** — suspect links are the whole point |
| `-W` no-review-check | Fresh import before initial review | **Never** after initial review pass |
| `-s PREFIX` | Quarantine a known-broken doc | Only if that doc is legitimately outside scope |

## What "valid" means for publishing

`doorstop publish` does its own minimal validation but won't catch every
issue. Treat `doorstop` exit-0 as a precondition for publishing a release
snapshot. For CI, gate on `scripts/doorstop_lint.sh` (wraps `doorstop -e`).
