# Publishing

`doorstop publish` renders a document (or the whole tree) to one of four
formats. Format selection is driven by explicit flags first, then by the
output file's extension, then by defaults.

## Subcommand shape

```
doorstop publish <prefix|all> [<path>]
                 [-t|-m|-l|-H]
                 [-w WIDTH]
                 [-C|--no-child-links]
                 [--no-levels {all|body}]
                 [--template FILE]
                 [--index]
```

Source: `doorstop/cli/main.py:509-546`.

## Format matrix

| Format | Flag | Extension auto-detect | Default for |
|---|---|---|---|
| Text | `-t`, `--text` | `.txt` | Stdout (no path) |
| Markdown | `-m`, `--markdown` | `.md` | — |
| LaTeX | `-l`, `--latex` | `.tex` | — |
| HTML | `-H`, `--html` | `.html` | `publish all <dir>` |

Rules:

- Explicit flag always wins.
- If no flag and `path` has a recognized extension, the extension picks the
  format.
- If no flag and no path, it's text to stdout.
- If no flag and `publish all <dir>` (directory), HTML.

## `publish all <dir>` — full tree

Generates a directory with:

- `index.html` — tree-wide TOC linking to each document.
- `<PREFIX>.html` per document.
- Assets (CSS, JS) for HTML output copied alongside.

```sh
doorstop publish all ./publish
```

After running, open `./publish/index.html` in a browser.

## Single-document publish

Two forms — the extension-driven form is easier to read:

```sh
# Extension picks the format:
doorstop publish REQ ./out/REQ.html
doorstop publish REQ ./out/REQ.md
doorstop publish REQ ./out/REQ.tex
doorstop publish REQ ./out/REQ.txt

# Flag picks the format:
doorstop publish REQ ./out/REQ -H           # HTML
doorstop publish REQ ./out/REQ -m           # Markdown
```

## Flags

| Flag | What it does | When to use |
|---|---|---|
| `-w WIDTH` | Wrap text output at WIDTH columns. Text/LaTeX only. | Constraining terminal output or diff-friendly plain text. |
| `-C`, `--no-child-links` | Omit the reverse-link annotations (children pointing up to this item). | You want a clean requirements spec without a traceability view mixed in. |
| `--no-levels all` | Strip every level number from output. | Publishing to a downstream tool that imposes its own numbering. |
| `--no-levels body` | Strip levels only from non-heading items. | Keep section numbers on headings, drop them on leaf requirements. |
| `--template FILE` | Use a custom Jinja2 (or format-specific) template. | Branded HTML, corporate LaTeX class, custom Markdown scaffolding. |
| `--index` | In Markdown mode, also produce a top-level `index.md`. | Publishing a docs-site-friendly tree of Markdown files. |

## Templates

Each publisher uses the format's native templating. Built-in templates live
under `doorstop/core/publishers/`. To customize:

1. Copy a built-in template to your project (e.g.
   `doorstop/core/publishers/templates/html/base.html`).
2. Edit.
3. Pass `--template <path-to-your-template>`.

HTML templates use Jinja2. LaTeX templates are passthrough `.tex` scaffolds.
Markdown has a small scaffold for `--index` mode.

## Traceability

The HTML publish output includes a per-document traceability sidebar by
default: each item shows its parent links and (unless `-C`) its child links.
For a cross-document traceability matrix, use the Python API:

```python
import doorstop
tree = doorstop.build()
matrix = tree.get_traceability()    # iterable of tuples (REQ, ..., TST)
```

Or use `doorstop publish all` and inspect the generated index, which links
through every item.

## `attributes.publish` — extended attributes in output

To include custom (extended) attributes in published output, list them in
the document's `.doorstop.yml`:

```yaml
attributes:
  publish:
    - invented-by
    - type
    - verification-method
```

Attributes in this list render as labeled rows beneath each item's text.
Requires doorstop v2.2+.

## Headings vs. normative items

- Heading: `level: X.0` + `normative: false`. Renders as a section header.
  Does not print a UID. Contributes to the outline but not to the
  requirements count.
- Normative item: `normative: true`. Renders with its UID and optional
  `header:` text, followed by `text:`.

Levels ending in `.0` with `normative: true` are still normative items, not
headings. The heading rule requires **both** `.0` level and `normative:
false`.

## `--linkify` (HTML mode)

When publishing HTML, doorstop linkifies UIDs within `text:` automatically:
if `REQ001` appears in a Markdown text block and `REQ001` exists in the
tree, it becomes a hyperlink. This is built-in — no flag to enable, no flag
to disable cleanly.

## Pre-publish checklist

Before `doorstop publish all`:

1. `doorstop` exits 0 (no WARNING/ERROR). Publishing a tree with suspect
   links is valid but meaningless.
2. Every edited item is `doorstop review`ed. Unreviewed items still publish
   but signal nothing about intent.
3. Commit the tree — you want the publish directory to correspond to a
   specific SHA.

## Output expectations for this skill

If the user asked to publish, the task is done when:

- The publish directory exists and contains the expected files.
- `index.html` (or the single output file) renders.
- The run produced no errors.

Never claim "publish succeeded" without confirming the artifact is on disk.
