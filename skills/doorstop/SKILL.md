---
name: doorstop
description: Use for Doorstop requirements work — creating/linking/validating/reviewing/publishing items, editing .doorstop.yml, authoring validators, or driving the doorstop CLI, Python API, or REST server.
---

# Doorstop

Doorstop is a version-controlled requirements management system. It stores
requirements as YAML or Markdown files (one file per item, one directory per
document), linked bidirectionally into a tree, validated for consistency, and
published to text/Markdown/HTML/LaTeX. Every state change has an exact
representation on disk, so git is the source of truth.

## When to use

- Creating, editing, linking, or deleting requirement items
- Bootstrapping a new `reqs/` or `tests/` tree in a repo
- Writing or updating `.doorstop.yml`, item YAML, or Markdown-frontmatter items
- Validating a tree (`doorstop`) and fixing warnings/errors
- Clearing suspect links or marking reviews (`doorstop clear`, `doorstop review`)
- Importing/exporting via CSV/TSV/XLSX for spreadsheet round-trip
- Publishing HTML, Markdown, LaTeX, or text snapshots
- Authoring a custom validator or validation hook
- Calling Doorstop from a Python script or using the REST server

## When not to use

- General Python, YAML, or Markdown authoring with no requirements-management
  dimension — use the base tools directly.
- Editing the internal `doorstop/` package code of this repo — that is software
  development on Doorstop itself, not *use* of Doorstop. Read the project's
  `CONTRIBUTING.md` instead.
- Driving the desktop GUI (`doorstop-gui`) — it is a Tkinter app and not agent-
  drivable.

## Core concepts (internalize these)

- **Tree** → **Document** → **Item** → **Link**. Each *document* is a directory
  holding a `.doorstop.yml` config and one item file per requirement. Items link
  *upward* (child → parent); the tree is bidirectional at runtime.
- **UID** = `<prefix><sep><number-or-name>`, e.g. `REQ001`, `REQ-001`, `TST_007`.
  `prefix`, `sep`, and `digits` are set in `.doorstop.yml`.
- **Fingerprint (reviewed)**: SHA-256 of `uid + text + ref + references + links`
  (plus any extended attrs listed under `attributes.reviewed`). Stored in the
  item's `reviewed:` field. *Never hand-edit it — use `doorstop review`.*
- **Suspect link**: a child's stored parent-fingerprint no longer matches the
  parent's current fingerprint. Clear with `doorstop clear`, not by re-reviewing.
- **Level**: outline position like `1.2.3`. `*.0` + `normative: false` ⇒ heading.
- Items are referenced by UID, not by filename. **UIDs are immutable** — renaming
  is delete + re-add + re-link.

## First move

When the user asks for any doorstop task, before mutating anything:

1. `git rev-parse --show-toplevel` — Doorstop requires a VCS root. If the user is
   outside one, say so and stop.
2. `doorstop` (no args) — if it prints a tree and exits 0, you have a working
   tree. If it errors with "no documents found", user is bootstrapping.
3. If you need a structured view, run
   `python scripts/doorstop_snapshot.py` (shipped with this skill) to get JSON.
4. Pick the right reference from the map below, read it, then act.

## Workflow map

| Task | Reference |
|---|---|
| Bootstrap a project / create a document | `references/workflows.md` |
| Add / edit / remove items | `references/cli-commands.md` + `references/file-formats.md` |
| Link items across documents | `references/workflows.md` |
| Validate / fix warnings / clear suspects / mark reviewed | `references/validation.md` |
| Publish HTML / Markdown / LaTeX / text | `references/publishing.md` |
| Round-trip via spreadsheet (CSV / TSV / XLSX) | `references/import-export.md` |
| Drive Doorstop from Python / write a script | `references/python-api.md` |
| REST API / integrations | `references/server-api.md` |
| Custom validator / hook / extension | `references/extensions.md` |
| Suspect links / unreviewed / cycles / skipped levels | `references/troubleshooting.md` |
| Every CLI flag + exact subcommand semantics | `references/cli-commands.md` |
| `.doorstop.yml` and item YAML/Markdown schemas | `references/file-formats.md` |

## Non-negotiables

- **Always `doorstop review` after editing item content.** Never write a
  `reviewed:` hash yourself — the hash function is SHA-256 over a specific
  ordered value set and *will* drift if you compute it wrong.
- **Prefer the CLI for mutations**, not manual YAML edits. `doorstop add` /
  `edit` / `link` / `unlink` / `remove` / `clear` / `review` enforce invariants
  that hand-edits skip.
- **Run `doorstop` after every batch of changes.** Validation is fast and the
  failure modes (suspect links, orphaned children, level gaps) are cheap to fix
  when caught immediately.
- **Never mix item formats within a single document.** A document's `itemformat`
  is set at `create` time and is effectively read-only after the first item.
- **Never rename an item's file.** The filename *is* the UID.
- **Level `X.0` + `normative: false` is a heading**, not a requirement. Don't
  link requirements to headings — validation will warn.
- **Derived items don't need parent links**; mark `derived: true` when the
  requirement has no upstream source.
- When generating a wave of items, use `doorstop add -c N` rather than looping —
  `add` reserves UIDs atomically through the server when one is running.

## Output expectations

A task is complete when:

- `doorstop` exits 0 (or only with `INFO`-level messages you explicitly accept).
- Every edited item has been passed through `doorstop review`.
- If the task called for publication, the publish artifact exists and contains
  the expected items (`index.html` + per-document files for `publish all`).
- Item files and `.doorstop.yml` files are committed (or staged) — remind the
  user to commit; doorstop state is meaningless outside version control.

## Reference map

Load references on demand — they are progressive-disclosure files, not always-on
context.

- `references/cli-commands.md` — every `doorstop` subcommand, every flag, canonical
  invocations, exit semantics, and when each command is (and isn't) the right tool.
- `references/python-api.md` — `doorstop.build`, `Tree`/`Document`/`Item`, exception
  hierarchy, iteration patterns, scripting examples, validation-hook signatures.
- `references/file-formats.md` — `.doorstop.yml` schema, YAML item schema,
  Markdown-frontmatter item schema, UID grammar, `references:` block, extended
  attributes, publish-list, `!include` tag.
- `references/workflows.md` — end-to-end recipes: bootstrap, add-child-document,
  link, review-after-churn, publish-release, bulk-import.
- `references/validation.md` — full INFO/WARNING/ERROR matrix, suspect-link
  mechanics, what each `-L/-R/-C/-Z/-S/-W/-w/-e` flag does, when skipping is OK.
- `references/publishing.md` — format matrix, `--template`, `--index`,
  `--no-child-links`, `--no-levels`, publish-all layout, traceability matrix.
- `references/import-export.md` — export formats, round-trip via XLSX, the
  "blank UID" new-item convention, `--map` for column renames.
- `references/server-api.md` — every REST endpoint with JSON shapes, how the
  `--server`/`--port`/`-f/--force` client flags affect item-number reservation.
- `references/extensions.md` — `extensions.item_validator` in `.doorstop.yml`,
  `tree.validate(document_hook=, item_hook=)`, `item_sha_required`, custom
  publishers, custom attributes.
- `references/troubleshooting.md` — decision tree for the most common failure
  modes with the exact commands to run.

## Scripts

- `scripts/doorstop_snapshot.py` — dumps the tree, documents, items, links,
  and validation issues as JSON. Use this when you want a structured view
  for agent reasoning rather than parsing CLI stdout.
- `scripts/doorstop_lint.sh` — CI-friendly wrapper: runs `doorstop -e` (errors
  on any warning) with sensible defaults, returns non-zero on any issue.

## Example tree

`assets/example_reqs/` is a tiny two-document example (`REQ` + `TST`, one link,
one heading) that validates clean. Copy it as a starting template, or read it to
confirm the canonical on-disk shape when you are unsure.
