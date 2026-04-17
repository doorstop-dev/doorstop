# Import and export

Export rehydrates a document as a portable file. Import pushes changes back.
The round trip is the primary integration path for spreadsheet-first
authors and for bulk edits from external tools.

## Format matrix

| Format | Export flag | Import format detection | Best for |
|---|---|---|---|
| YAML | `-y` / `--yaml` | `.yml`, `.yaml` | Scripting, diffing, machine round-trip |
| CSV | `-c` / `--csv` | `.csv` | Git-friendly spreadsheet |
| TSV | `-t` / `--tsv` | `.tsv` | Spreadsheet with tab-separated columns |
| XLSX | `-x` / `--xlsx` | `.xlsx` | Excel/LibreOffice authoring |

Sources: `doorstop/cli/main.py:487-506` (export), `:448-484` (import).

## Export

```sh
doorstop export REQ /tmp/req.xlsx            # explicit path + extension
doorstop export REQ                          # stdout, YAML (default with no path)
doorstop export all /tmp/out                 # every document to a directory
```

### `-w/--width` (text-ish output)

Wraps exported text columns. Applies to formats that render free text
columns (CSV/TSV), not XLSX cells.

### `all` special prefix

`doorstop export all <dir>` emits one file per document into `<dir>`.
Default format for `all` is CSV if no format flag or extension is
detectable.

## Import

```sh
doorstop import /tmp/req.xlsx REQ            # positional form
doorstop import --document REQ ./imported/   # create a new document from path
doorstop import --item REQ REQ042 -a level=1.5 -a normative=true
```

Source: `doorstop/cli/main.py:448-484`.

### The three import modes

| Mode | Form | What it does |
|---|---|---|
| Round-trip (file) | `doorstop import <path> <prefix>` | Reads file, creates new items for blank UIDs, updates existing for known UIDs. |
| New document | `doorstop import --document PREFIX PATH [-p PARENT]` | Registers an already-laid-out directory of item files as a doorstop document. |
| New item | `doorstop import --item PREFIX UID -a key=value [-a ...]` | Creates one item with the given UID and attribute overrides. |

Only one of `--document` or `--item` can be passed.

### Round-trip: the blank-UID convention

In a spreadsheet import, any row whose UID column is **blank** is treated
as a new item. Doorstop reserves a fresh UID (through the server if
running, otherwise locally) and creates the item with the row's attribute
values. Rows with existing UIDs are updated in place.

After any import, the touched items are left **unreviewed** — the whole
point is that content changed. Run `doorstop review <uid>` (or `doorstop
review <prefix> -d` for the whole document) once you've confirmed the
import is what you wanted.

### `-a key=value` attribute overrides

Repeatable. On `--item` mode, sets attributes at create time. On round-trip
mode, can be used as fallbacks for columns the spreadsheet omitted.

Common keys: `level`, `normative`, `active`, `derived`, `header`, or any
custom extended attribute.

### `-m/--map` column renames

When the spreadsheet's column names don't match doorstop's attribute names:

```sh
doorstop import /tmp/req.xlsx REQ -m "{'Requirement': 'text', 'Tag': 'type'}"
```

The argument is a Python-literal dict (use single quotes inside double
quotes on the shell). Every occurrence of `Requirement` in the spreadsheet
header row is read as `text`, and `Tag` is read as custom attribute `type`.

### `-p PARENT` — only with `--document`

When creating a document from a directory, sets the parent prefix (same as
the `--parent` flag on `doorstop create`).

## Round-trip recipe

```sh
doorstop export REQ /tmp/req.xlsx
# Edit /tmp/req.xlsx in Excel/LibreOffice.
# - Change text cells freely.
# - Add new rows with a blank UID column → they become new items.
# - Never edit the `reviewed` column by hand.
doorstop import /tmp/req.xlsx REQ
doorstop                                      # validate
doorstop review REQ -d                        # mark the whole document reviewed
```

Before importing a spreadsheet authored by someone else, **diff** it
against a fresh export of the live tree — spreadsheet tools often eat
newlines, coerce numbers, or strip leading zeros.

## Import a whole document from a directory

Scenario: someone handed you a folder of YAML files laid out in doorstop's
format, but never registered as a document.

```sh
doorstop import --document REQ /path/to/their/reqs
```

Equivalent to: create the `.doorstop.yml` if missing, register every
matching file as an item.

## Import a single item

```sh
doorstop import --item REQ REQ042 -a text="the rule" -a level=2.3 -a normative=true
```

Useful for scripted creation when `doorstop add` doesn't fit (e.g. you need
a specific UID).

## Gotchas

- **Leading zeros**: Excel drops `001` → `1`. If your `digits: 3` and a UID
  becomes `REQ1`, doorstop will treat it as a new item (or error) because
  the filename no longer matches the UID grammar. Format the UID column as
  text in Excel before editing.
- **Line endings**: CSV from Windows has CRLF, from Mac has LF. Doorstop
  handles both, but git diffs will be noisy. Use `.gitattributes` if you
  commit CSV.
- **Multi-line text**: CSV encodes newlines within a cell as `\n` inside
  quoted strings. Excel mostly gets this right. LibreOffice mostly gets it
  right. Script-generated CSV needs care.
- **Extended attributes**: preserved on round-trip only if they appear as
  columns. Adding a new column ≈ adding a new extended attribute. Remove a
  column to drop it from all items (dangerous; prefer targeted edits).
- **`reviewed` column**: exported but **never re-imported as-is**. Doorstop
  clears the stamp on re-import because content may have changed.

## Programmatic alternatives

If the spreadsheet middleware is painful, use the Python API directly
(`references/python-api.md`): `doorstop.importer.import_file`,
`doorstop.exporter.export`, or iterate `Item` objects and set attributes.
Scripts are easier to review than hand-edited XLSX.
