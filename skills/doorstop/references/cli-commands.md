# CLI Commands Reference

Every `doorstop` subcommand with its exact flags, canonical invocations, and
when to reach for it.

## Global invocation

```
doorstop [global-options] [<subcommand> [subcommand-options] [args]]
```

With no subcommand, `doorstop` validates the tree and prints the hierarchy.
Exits 0 on success, 1 on validation failure or any error.

### Global options (apply to every subcommand)

| Flag | Effect |
|---|---|
| `-j PATH`, `--project PATH` | Project root (default: auto-detected via VCS) |
| `-v, --verbose` | Increase logging (stackable: `-vv`, `-vvv`) |
| `-q, --quiet` | Errors and prompts only |
| `-V, --version` | Print version and exit |
| `--server HOST` | Point at a running `doorstop-server` for UID reservation |
| `--port NUMBER` | Server port (default 7867) |
| `-f, --force` | Perform the action without the server (don't reserve UIDs) |

### Validation options (apply to the bare `doorstop` invocation)

| Flag | Effect |
|---|---|
| `-F, --no-reformat` | Don't rewrite item files to canonical form |
| `-r, --reorder` | Auto-reorder item levels during validation |
| `-L, --no-level-check` | Skip level-gap / duplicate-level checks |
| `-R, --no-ref-check` | Skip external-reference resolution |
| `-C, --no-child-check` | Skip child-link (reverse-link) checks |
| `-Z, --strict-child-check` | *Require* child links from every document below |
| `-S, --no-suspect-check` | Skip suspect-link checks |
| `-W, --no-review-check` | Skip unreviewed-item checks |
| `-s PREFIX, --skip PREFIX` | Skip a document (repeatable) |
| `-w, --warn-all` | Escalate `INFO` to `WARNING` |
| `-e, --error-all` | Escalate `WARNING` to `ERROR` (non-zero exit) |

See `references/validation.md` for when each flag is safe.

---

## `doorstop` (no subcommand)

Validates the tree. Runs cycle detection, level checks, link resolution,
suspect-link checks, and review-status checks.

```
doorstop                     # full validation
doorstop -e                  # CI mode: warnings become errors
doorstop -s REQ -s TST       # skip two documents
doorstop --no-suspect-check  # quick structural check ignoring staleness
```

Exits 0 iff the tree is valid under the active flags.

---

## `doorstop create PREFIX PATH`

Create a new document directory (writes `PATH/.doorstop.yml`).

| Flag | Default | Effect |
|---|---|---|
| `-p PREFIX, --parent PREFIX` | none (root doc) | Parent document's prefix |
| `-i {yaml,markdown}, --itemformat` | `yaml` | Item file format (set *once*) |
| `-d N, --digits N` | `3` | Zero-padded UID digit count |
| `-s SEP, --separator SEP` | `""` | Separator in UIDs; only `-`, `_`, `.` allowed |

```
doorstop create REQ ./reqs                                 # root doc
doorstop create TST ./tests --parent REQ                   # child of REQ
doorstop create LLR ./reqs/llr --parent REQ -d 4 -s _      # LLR_0001
doorstop create SPEC ./spec -i markdown                    # markdown items
```

Fails if `.doorstop.yml` already exists, if `sep` uses a forbidden character,
or if `parent` doesn't resolve.

---

## `doorstop delete PREFIX`

Delete the named document and every item in it. Destructive — confirm first.

```
doorstop delete TST
```

---

## `doorstop add PREFIX`

Create a new item file in a document. Without `--edit`, the file is created
populated with defaults and saved.

| Flag | Effect |
|---|---|
| `-l LEVEL, --level LEVEL` | Desired level (e.g. `1.2.3`); auto-computed if omitted |
| `-n NANU, --name NANU`, `--number NANU` | Use this name/number instead of auto-increment |
| `-c N, --count N` | Create N items (default 1) |
| `--edit` | Open the new item in `$EDITOR` after creating |
| `-T PROGRAM, --tool PROGRAM` | Override `$EDITOR` for `--edit` |
| `-d FILE, --defaults FILE` | YAML file with default attribute values |
| `--noreorder` | Don't reorder sibling levels after add |

```
doorstop add REQ                    # next auto-numbered UID, default level
doorstop add REQ -c 5               # add 5 items
doorstop add REQ -l 2.1.3           # specific level
doorstop add REQ -n login           # UID = REQ-login (requires non-empty sep)
doorstop add REQ --edit             # open in editor after create
```

Without a running `doorstop-server`, UID reservation is local. With `--server`,
Doorstop reserves via `POST /documents/<prefix>/numbers`.

---

## `doorstop remove UID`

Delete a single item by UID. Does **not** unlink it first — if anything links
to it, the link becomes dangling and validation will error.

```
doorstop remove REQ042
```

Always `doorstop unlink` first if there are children.

---

## `doorstop edit LABEL`

Edit an item (by UID) or a whole document (by prefix).

| Flag | Effect |
|---|---|
| `-a, --all` | Edit the whole item (YAML), not just the `text:` field |
| `-i, --item` | Force `label` to be parsed as an item UID |
| `-d, --document` | Force `label` to be parsed as a document prefix |
| `-y, --yaml` | When editing a document, round-trip through YAML (default) |
| `-c, --csv` | Round-trip through CSV |
| `-t, --tsv` | Round-trip through TSV |
| `-x, --xlsx` | Round-trip through XLSX |
| `-T PROGRAM, --tool` | Override `$EDITOR` |

Item edits lock the file via the VCS integration to prevent concurrent writes.

```
doorstop edit REQ001            # edit text only
doorstop edit REQ001 -a         # edit all attributes
doorstop edit REQ -d -x         # dump REQ to XLSX, open editor, re-import
```

When editing a whole document, Doorstop exports → opens → re-imports and then
offers to delete the intermediate file.

---

## `doorstop reorder PREFIX`

Organize a document's outline. Three modes:

- Default (no flags): generate an `index.yml` in the document directory, open
  it in `$EDITOR` for manual editing, then re-import.
- `-a, --auto`: auto-shift levels to eliminate duplicates and gaps without an
  index file.
- `-m, --manual`: manual mode; do not auto-fix after reading the index.

| Flag | Effect |
|---|---|
| `-a, --auto` | Pure auto (no index interaction) |
| `-m, --manual` | Pure manual (no auto-fix after index) |
| `-T PROGRAM, --tool` | Override `$EDITOR` |

```
doorstop reorder REQ -a         # auto-fix duplicate/skipped levels
doorstop reorder REQ            # generate index.yml, edit by hand, re-import
```

---

## `doorstop link CHILD PARENT`

Add a traceability link from `CHILD` to `PARENT` (both UIDs). Fails on
self-links, cycles, and missing items.

```
doorstop link TST007 REQ023
```

## `doorstop unlink CHILD PARENT`

Remove the link. Fails silently-with-warning if the link did not exist.

```
doorstop unlink TST007 REQ023
```

---

## `doorstop clear LABEL [PARENTS...]`

Mark suspect links as cleared. `LABEL` is an item UID, a document prefix, or
`all`. Optional positional `PARENTS` narrow the clearing to specific parents.

| Flag | Effect |
|---|---|
| `-i, --item` | Force `label` as item UID |
| `-d, --document` | Force `label` as document prefix |

```
doorstop clear TST007                  # clear TST007's suspects from all parents
doorstop clear TST007 REQ023 REQ024    # only to those parents
doorstop clear TST                     # clear every item in TST
doorstop clear all                     # nuclear: clear everything
```

Clearing updates the stored parent-fingerprint to the *current* parent
fingerprint — it does **not** change the item's own `reviewed:` hash.

---

## `doorstop review LABEL`

Mark an item, document, or the whole tree as reviewed. Rewrites `reviewed:` to
the current fingerprint.

| Flag | Effect |
|---|---|
| `-i, --item` | Force `label` as item UID |
| `-d, --document` | Force `label` as document prefix |

```
doorstop review REQ001
doorstop review REQ
doorstop review all
```

If `.doorstop.yml` has `extensions.item_sha_required: true`, `review` also
updates the `sha:` on every external file reference.

---

## `doorstop import PATH PREFIX`

Three disjoint modes selected by argument shape:

```
# Mode 1: import items from an exported file into an existing document
doorstop import items.xlsx REQ
doorstop import items.csv REQ -m "{'Requirement': 'text'}"

# Mode 2: register a pre-existing document directory
doorstop import -d REQ ./reqs -p SYS     # -p = parent

# Mode 3: create a specific item by UID (backfill)
doorstop import -i REQ REQ042 -a "{'text': 'Legacy item.'}"
```

| Flag | Effect |
|---|---|
| `-d PREFIX PATH, --document PREFIX PATH` | Mode 2 |
| `-i PREFIX UID, --item PREFIX UID` | Mode 3 |
| `-p PREFIX, --parent PREFIX` | Parent prefix (mode 2) |
| `-a DICT, --attrs DICT` | Python-literal dict of item attributes |
| `-m DICT, --map DICT` | Python-literal dict mapping source → Doorstop attr names |

Supported extensions for mode 1: `.yml`, `.csv`, `.tsv`, `.xlsx`.

In XLSX round-trip, **leave the UID cell blank to create a new item**. Never
rename an existing UID.

---

## `doorstop export PREFIX [PATH]`

Export a single document or `all` documents. Without `PATH`, writes to stdout.

| Flag | Default per ctx | Effect |
|---|---|---|
| `-y, --yaml` | default (no path) | YAML |
| `-c, --csv` | default for `all` | CSV |
| `-t, --tsv` | | TSV |
| `-x, --xlsx` | | XLSX |
| `-w N, --width N` | | Line width on text |

```
doorstop export REQ                    # YAML to stdout
doorstop export REQ REQ.xlsx           # XLSX file
doorstop export all ./out              # one CSV per document in ./out
```

Note: `all` cannot be displayed to stdout.

---

## `doorstop publish PREFIX [PATH]`

Publish to a human-readable format. `PREFIX` can be `all`. Without `PATH`,
writes to stdout.

| Flag | Default per ctx | Effect |
|---|---|---|
| `-t, --text` | default (no path) | Plain text |
| `-m, --markdown` | | Markdown |
| `-l, --latex` | | LaTeX |
| `-H, --html` | default for `all` | HTML |
| `-w N, --width N` | | Line width on text |
| `-C, --no-child-links` | | Omit reverse-link sections |
| `--no-levels {all,body}` | | Hide levels on {everything, body items only} |
| `--template FILE` | | Custom template (HTML/Markdown) |
| `--index` | | Generate top-level index (Markdown/HTML) |

```
doorstop publish REQ REQ.html
doorstop publish REQ REQ.md -m
doorstop publish all ./publish                   # multi-doc HTML with index
doorstop publish all ./publish --index           # force-generate index
doorstop publish REQ -m --no-child-links         # Markdown to stdout, no reverse-links
```

`publish all <dir>` produces:

```
<dir>/
├── index.html              # top-level index linking all docs
├── traceability.csv        # matrix of parent↔child links (when applicable)
└── documents/
    ├── REQ.html
    ├── TST.html
    └── assets/             # copied from each document's assets/
```

See `references/publishing.md` for template authoring and the matrix format.

---

## Subcommand semantics quick-reference

| Command | Mutates disk | Mutates VCS | Needs server | Typical exit |
|---|---|---|---|---|
| `doorstop` | no (read-only unless `-F`/`-r`) | no | no | 0 valid, 1 invalid |
| `create` | yes (new dir + config) | no | no | 0 / 1 |
| `delete` | yes (removes dir) | no | no | 0 / 1 |
| `add` | yes (new file) | no | optional (UID reservation) | 0 / 1 |
| `remove` | yes (removes file) | no | no | 0 / 1 |
| `edit` | yes | locks via VCS | no | 0 / 1 |
| `reorder` | yes (levels) | no | no | 0 / 1 |
| `link` / `unlink` | yes (child file) | no | no | 0 / 1 |
| `clear` / `review` | yes (item fields) | no | no | 0 / 1 |
| `import` | yes | no | optional | 0 / 1 |
| `export` / `publish` | yes (output only) | no | no | 0 / 1 |

## When **not** to reach for each command

- `delete PREFIX` — if you actually want to move the document, there is no
  rename; delete + recreate + re-import is the only path.
- `remove UID` — if children link to it; `unlink` first.
- `clear` — if the parent *actually changed meaningfully* and you want the
  child to flag unreviewed; in that case do `review` on the parent, then
  re-review the child intentionally instead of masking with `clear`.
- `--no-suspect-check`, `--no-review-check` — in CI. These turn off the very
  checks requirements management exists to enforce.
