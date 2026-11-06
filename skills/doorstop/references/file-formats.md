# File formats

This is the authoritative on-disk reference: `.doorstop.yml` for documents,
YAML or Markdown-with-frontmatter for items, and the surrounding conventions
(UIDs, `references:`, extended attributes, `!include`).

Prefer the CLI for mutations. Hand-edits are for schema-level things the CLI
doesn't expose: extending `attributes.defaults`, `attributes.reviewed`,
`attributes.publish`, `extensions`, or switching `sep`.

## Document: `.doorstop.yml`

Every document directory contains exactly one `.doorstop.yml` file. Everything
else in the directory is either an item file or child content.

```yaml
settings:
  prefix: REQ          # mandatory, read-only after first item
  sep: ''              # mandatory, read-only after first item ('' or '-' or '_')
  digits: 3            # mandatory, read-only
  parent: SYS          # optional; set by `doorstop create --parent SYS`
  itemformat: yaml     # 'yaml' (default) or 'markdown' — read-only after first item
attributes:
  defaults:            # optional — default values for extended attributes
    type: functional
    verification-method: test
  reviewed:            # optional — extended attrs that feed the fingerprint
    - type
    - verification-method
  publish:             # optional — extended attrs that appear in published output
    - invented-by
    - type
extensions:            # optional — per-document validator hooks and flags
  item_validator: validators/req_validator.py   # path to .py file, relative to .doorstop.yml
  item_sha_required: true                       # require `sha` on each `references:` entry
```

### `settings` keys

| Key | Required | Read-only after first item | Default | Meaning |
|---|---|---|---|---|
| `prefix` | yes | yes | — | UID prefix. e.g. `REQ`, `TST`, `LLR`. Must be unique across the tree. |
| `sep` | yes | yes | `''` | Separator between prefix and number. `''` → `REQ001`; `-` → `REQ-001`; `_` → `REQ_001`. |
| `digits` | yes | yes | `3` | Zero-padding width for numeric UIDs. |
| `parent` | no | yes | — | Prefix of parent document. Set by `doorstop create -p`. Root document has no parent. |
| `itemformat` | yes | yes | `yaml` | `yaml` or `markdown`. Mixing within one document is forbidden. |

"Read-only after first item" = changing these values will strand or break
existing items. Decide `prefix` / `sep` / `digits` / `itemformat` at `create`
time and do not revisit.

### `attributes` keys

| Key | Type | Purpose |
|---|---|---|
| `defaults` | mapping | Fallback values for extended attributes that don't appear in an item file. |
| `reviewed` | list of strings | Extended attribute names whose values feed the `reviewed:` fingerprint. |
| `publish` | list of strings | Extended attribute names to render in publish output (since v2.2). |

### `extensions` keys

| Key | Type | Purpose |
|---|---|---|
| `item_validator` | path | Python file (relative to the document dir) that exports `item_validator(item)`. Called on every item during `tree.validate()`. |
| `item_sha_required` | bool | When true, each entry in `references:` must carry a `sha:` field. `doorstop review` inserts the SHA if missing. |

### `!include` composition

Inside `.doorstop.yml` you can pull content from a sibling YAML file with the
`!include` tag. Paths are relative to the file containing the tag. Absolute
paths are not supported.

```yaml
# .doorstop.yml
attributes:
  defaults:
    text: !include templates/boilerplate-text.yml
```

```yaml
# templates/boilerplate-text.yml
|
  Shared boilerplate that many items start from.
  Multi-line YAML block scalar.
```

Use `!include` for large repeated defaults or template text — not for item
content itself.

## Item: YAML format

Filename = UID + `.yml` or `.yaml`. The filename (minus extension) **is** the
UID. Never rename an item file — the UID is immutable.

```yaml
active: true
derived: false
header: |
  Identifiers
level: 2.1
links:
  - REQ010: null                               # bare-UID form also legal: `- REQ010`
  - REQ011: avwblqPimDJ2OgTrRCXxRPN8FQhUBWqPIXm7kSR95C4=
normative: true
ref: ''                                        # legacy single-reference string
references:                                    # new-style array of external refs
  - path: src/sensors/temp.c
    type: file
  - path: tests/test_temp.c
    type: file
    keyword: REQ-TEMP                          # optional — grep-like line search
    sha: 28c16553...                           # required when item_sha_required: true
reviewed: 9TcFUzsQWUHhoh5wsqnhL7VRtSqMaIhrCXg7mfIkxKM=
text: |
  Doorstop **shall** provide unique and permanent identifiers to linkable
  sections of text.

# Custom extended attributes follow — any valid YAML below this point is fair
# game. Values can be scalars, lists, or mappings.
invented-by: jane@example.com
type: functional
verification-method: test
```

### Standard attributes

| Attr | Type | Default | In fingerprint? | Meaning |
|---|---|---|---|---|
| `active` | bool | `true` | no | `false` hides the item from publish and skips validation. |
| `derived` | bool | `false` | no | `true` = no upstream source required; validation won't complain about missing parent link. |
| `normative` | bool | `true` | no | `false` + `level` ending in `.0` = heading. Headings aren't linked or validated as requirements. |
| `level` | outline | `1.0` | no | Presentation order, e.g. `1.2.3`. Quote non-float values: `level: '1.10'`. |
| `header` | text | `''` | no | Short title shown next to UID in published output. Different from a heading item. |
| `text` | text | `''` | **yes** | Main body. Markdown. Multi-line via `|` or `>-`. |
| `ref` | string | `''` | **yes** | Legacy single reference (file or keyword). Prefer `references:`. |
| `references` | list | `null` | **yes** | Array of external refs. See table below. |
| `links` | list | `[]` | UIDs only | Parent UIDs (child → parent direction). Fingerprints are stored but don't feed the item's own fingerprint. |
| `reviewed` | stamp | `null` | — | Stored SHA-256 (url-safe Base64) of the fingerprint at last review. **Never hand-edit.** |

### `references:` entry shape

Each entry is a mapping:

| Key | Required | Meaning |
|---|---|---|
| `path` | yes | Relative path from repo root to the referenced file. |
| `type` | yes | Currently always `file`. |
| `keyword` | no | If set, doorstop also grep-searches the file for this keyword and records the matching line. |
| `sha` | no (unless `item_sha_required: true`) | SHA-256 of the referenced file's content. `doorstop review` fills this. |

### UID grammar

```
UID   := PREFIX SEP (NUMBER | NAME)
PREFIX := starts with a letter, alphanumeric + '_' (no SEP chars)
SEP    := '' | '-' | '_' (from .doorstop.yml)
NUMBER := zero-padded decimal, width = settings.digits
NAME   := arbitrary string without SEP — used for named items
```

Examples: `REQ001` (`sep: ''`, `digits: 3`), `REQ-001` (`sep: '-'`), `TST_007`
(`sep: '_'`), `REQ-login-flow` (named item).

### Fingerprint computation

The `reviewed:` stamp is SHA-256 (URL-safe Base64) over a canonical
serialization of, in order:

1. `uid`
2. `text`
3. `ref`
4. `references` (full list including `path`, `type`, `keyword`, `sha`)
5. `links` — UIDs only (not the stored link fingerprints)
6. Any extended attribute listed in `attributes.reviewed` (in the order listed)

Attributes **not** in this set — `active`, `derived`, `normative`, `level`,
`header`, custom attrs not in `attributes.reviewed` — do **not** affect the
stamp. Changing them does not mark the item unreviewed.

Do not compute this yourself. Use `doorstop review <uid>`.

### Legacy `ref` vs new `references`

Both can coexist. New items should prefer `references:`. The legacy `ref`
string is still supported and checked:

- `ref: 'src/foo.c'` — filename search in project tree; first match wins.
- `ref: 'MY-KEYWORD'` — grep-like search across text files; first hit wins.

If a referenced file/keyword is unresolved, validation fails with an ERROR
unless `-r/--no-ref-check` is passed.

## Item: Markdown-with-frontmatter format

Filename = UID + `.md`. Selected with `itemformat: markdown` in `.doorstop.yml`
at document creation time.

```markdown
---
active: true
derived: false
level: 2.1
links:
  - REQ010: null
normative: true
ref: ''
reviewed: 9TcFUzsQWUHhoh5wsqnhL7VRtSqMaIhrCXg7mfIkxKM=
---

# Identifiers

Doorstop **shall** provide unique and permanent identifiers to linkable
sections of text.
```

Rules specific to this format:

- Frontmatter (between `---` fences) holds every attribute **except** `text`
  and `header`.
- The body below the frontmatter is the `text` value.
- The first `# heading` line in the body is parsed out as `header` and
  stripped from `text`. Any subsequent headings stay in `text`.
- Everything else — fingerprint rules, validation, linking, levels —
  behaves exactly as in the YAML format.
- Two documents in the same tree can use different `itemformat`s, but every
  item inside a given document must match that document's format.

## Extended attributes

Any key that isn't in the standard list is an "extended attribute". They are:

- Preserved as-is on save.
- Excluded from published output by default — add them to
  `attributes.publish` to render them.
- Excluded from the fingerprint by default — add them to
  `attributes.reviewed` to pull them in.
- Optionally defaulted via `attributes.defaults`.

Common uses: `type`, `verification-method`, `owner`, `ticket`, `priority`.

## Do / Don't

- **Do** let `doorstop create` / `add` / `edit` / `link` / `review` write
  these files. They know about format, fingerprint, and link invariants.
- **Do** hand-edit `.doorstop.yml` when changing `attributes.defaults`,
  `attributes.reviewed`, `attributes.publish`, or `extensions`. No CLI for
  these.
- **Don't** hand-edit `reviewed:` stamps. They drift, and validation will
  tell on you.
- **Don't** rename item files. The filename is the UID; to rename, `remove`
  the old UID and `add` a new one and re-link.
- **Don't** mix `itemformat` within a single document. Set it at `create`
  time and leave it.
- **Don't** set `sep` or `digits` after items exist. Filename-to-UID parsing
  will stop matching the old files.
- **Don't** assume ordering of YAML keys matters. It doesn't — doorstop
  re-sorts on save.
