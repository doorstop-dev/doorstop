# Python API Reference

Drive Doorstop from a Python script or REPL. Use the API when the CLI can't
express what you need — bulk programmatic changes, custom reports, validation
hooks, integrations.

## Getting started

```python
import doorstop

tree = doorstop.build()            # build from cwd (walks up to VCS root)
tree = doorstop.build(root="/abs/path/to/project")   # explicit root

print(tree)                        # one-line tree representation
print(tree.draw())                 # ASCII/box tree
print(len(tree.documents))
```

`build()` walks the VCS root, discovers every `.doorstop.yml`, and constructs a
`Tree`. It does **not** load item contents eagerly — call `tree.load()` if you
want to force it.

## Public surface

Importable from the top-level `doorstop` package:

| Name | What it is |
|---|---|
| `doorstop.build` | Build the tree from a project root |
| `doorstop.find_document(prefix)` | Find a document without an explicit tree |
| `doorstop.find_item(uid)` | Find an item without an explicit tree |
| `doorstop.Tree` | Tree class |
| `doorstop.Document` | Document class |
| `doorstop.Item` | Item class |
| `doorstop.builder` | Module with `build`, `_get_tree` |
| `doorstop.editor` | Editor launcher (`editor.edit`) |
| `doorstop.exporter` | `export()`, `export_lines()`, `check()` |
| `doorstop.importer` | `import_file()`, `create_document()`, `add_item()` |
| `doorstop.publisher` | `publish()`, `publish_lines()`, `check()` |
| `doorstop.DoorstopError` | Hard error |
| `doorstop.DoorstopWarning` | Warning |
| `doorstop.DoorstopInfo` | Info-level message |

`DoorstopFileError` lives at `doorstop.common.DoorstopFileError`.

## `Tree`

```python
tree = doorstop.build()

# Lookups
req = tree.find_document("REQ")             # DoorstopError if missing
item = tree.find_item("REQ042")              # DoorstopError if missing

# Enumeration
for document in tree:                        # iterates documents
    for item in document:
        ...

tree.documents                                # list, same as list(tree)

# Mutations
doc = tree.create_document(
    path="./reqs",
    value="REQ",         # prefix
    sep="-",
    digits=3,
    parent=None,
    itemformat="yaml",   # or "markdown"
)
item = tree.add_item("REQ", level="1.2", number=None)
tree.remove_item("REQ042")
child, parent = tree.link_items("TST007", "REQ023")
child, parent = tree.unlink_items("TST007", "REQ023")

# Validation
ok = tree.validate(skip=["OLD"], document_hook=None, item_hook=None)
for issue in tree.get_issues(skip=["OLD"]):   # yields DoorstopInfo/Warning/Error
    print(issue)

# Traceability
rows = tree.get_traceability()                # list of tuples (Item | None, ...)

# Structure
tree.draw()                                   # human tree diagram
tree.draw(encoding="utf-8")                   # force encoding
tree.draw(html_links=True)                    # emit <a> tags (server use)

# Delete EVERYTHING (destructive)
tree.delete()
```

**`tree.validate(...)`** returns `True` iff no `DoorstopError` was yielded; any
number of `DoorstopWarning`s or `DoorstopInfo`s don't flip the flag. The flag
set comes from `doorstop.settings`; CLI flags map there.

## `Document`

Defined in `doorstop.core.document.Document`. A document is a directory with a
`.doorstop.yml` config.

```python
doc = tree.find_document("REQ")

# Config
doc.prefix          # "REQ"
doc.sep             # "" or "-" or "_" or "."
doc.digits          # 3 (default)
doc.parent          # parent prefix or ""
doc.itemformat      # "yaml" or "markdown"
doc.extensions      # dict from .doorstop.yml
doc.extended_reviewed  # list[str] of attrs contributing to fingerprint

# Paths
doc.path            # absolute path to document dir
doc.root            # absolute path to project root
doc.relpath         # path relative to project root
doc.config          # path to .doorstop.yml
doc.assets          # path to assets/ or None
doc.template        # path to template/ or None

# Items
for item in doc:                 # yields ALL items (active + inactive)
    ...
doc.items                         # sorted list of ACTIVE items
len(doc)                          # count of active items
doc.find_item("REQ042")          # DoorstopError if missing or inactive
doc.next_number                   # integer (consults server if configured)
doc.depth                         # max level depth

# Mutations
item = doc.add_item(level=None, number=None, name=None, defaults=None, reorder=True)
doc.remove_item("REQ042", reorder=True)
doc.reorder(manual=True, automatic=True, start=None, keep=None)
doc.save()                        # rewrite .doorstop.yml
doc.load(reload=True)             # re-read from disk
doc.delete()                      # recursively delete

# Skip flag
doc.skip                          # True if a .doorstop.skip file sits in doc dir
```

### Document-level `extensions`

Values come from `.doorstop.yml`'s `extensions:` block. Doorstop reads:

| Key | Meaning |
|---|---|
| `item_validator` | Path (relative to `.doorstop.yml`) to a Python file exposing `item_validator(item)`. See `references/extensions.md`. |
| `item_sha_required` | `true` ⇒ `references[*].sha` is included in the stamp and updated on `review`. |
| `item_sha_buffer_size` | Read-buffer size when hashing reference files (default 65536). |

Unknown keys live in `doc.extensions` untouched; extensions you write can read
from there.

## `Item`

Defined in `doorstop.core.item.Item`. One item = one file.

```python
item = tree.find_item("REQ042")

# Identity & file location
item.uid            # UID object; str() → "REQ042"
item.path           # absolute path to .yml or .md file
item.relpath        # relative to project root
item.document       # parent Document

# Core attributes (all auto-load, most auto-save on set)
item.level          # Level object; str(item.level) → "1.2.3"
item.active         # bool
item.derived        # bool
item.normative      # bool
item.heading        # computed: level ends in .0 AND not normative
item.text           # Text object (str-like)
item.header         # Text (for headings or titled items)
item.ref            # legacy single string ref (deprecated)
item.references     # list of {"path": str, "type": "file", "keyword"?: str, "sha"?: str}
item.links          # sorted list of parent UIDs (UID objects)
item.parent_links   # alias for links

# Reviewed / cleared state
item.reviewed       # True iff stored reviewed stamp == current stamp(links=True)
item.cleared        # True iff no link parent-fingerprint is stale
item.stamp()        # current fingerprint
item.stamp(links=True)  # includes link UIDs (used for "reviewed")

# Traversal
item.parent_items       # list[Item]
item.parent_documents   # usually [parent-document]
item.child_items        # list[Item] (reverse links, FIRST level only)
item.child_links        # list[UID]
item.child_documents    # list[Document]

# Custom attributes (anything in the YAML not in the standard set)
item.attribute("invented-by")   # None if missing
# OR directly via the backing data:
item.data                        # dict for YAML dumping

# Mutations (auto-save)
item.level = "1.2.3"
item.text = "New text."
item.active = False
item.links = ["REQ023", "REQ024"]       # replaces entire set
item.link("REQ099")                       # adds one
item.unlink("REQ023")                     # removes one
item.references = [{"path": "src/foo.py", "type": "file"}]
item.set_attributes({"invented-by": "alice@example.com"})

# Review / clear
item.review()           # update stored reviewed stamp; also refreshes ref shas if item_sha_required
item.clear()            # absolve all suspect links
item.clear(parents=["REQ023"])  # only for that parent

# External refs
path, line = item.find_ref()       # legacy ref
found = item.find_references()     # new array form

# Delete
item.delete()

# Edit (spawns $EDITOR)
item.edit(tool=None, edit_all=False)   # edit_all=True → full YAML; False → text only
```

### `UID`, `Level`, `Stamp`, `Text`, `Prefix`

Defined in `doorstop.core.types`. You rarely construct these by hand; pass
plain strings and Doorstop wraps them. Key behavior:

- `UID("REQ-042")` ⇒ parses prefix/sep/number. `uid.prefix`, `uid.number`,
  `uid.name`, `uid.stamp` (link fingerprint).
- `Level("1.2.3")` — addition/shifts supported (`+ 1`, `>> 1`, `<< 1`).
  Heading flag `.heading` when `.0`.
- `Stamp(*values)` — SHA-256 of URL-safe base64 over the joined string
  representation of all values.
- `Text("...")` — like `str` but preserves paragraph structure for YAML dump.

## Scripting patterns

### Read-only report

```python
import doorstop

tree = doorstop.build()
for document in tree:
    active = [i for i in document if i.active]
    unreviewed = [i for i in active if not i.reviewed]
    print(f"{document.prefix}: {len(active)} active, {len(unreviewed)} unreviewed")
```

### Bulk attribute update (safe: use `set_attributes`)

```python
import doorstop

tree = doorstop.build()
for item in tree.find_document("REQ"):
    if not item.attribute("priority"):
        item.set_attributes({"priority": "medium"})
# After this, you'll want to:  doorstop review REQ
```

### Bulk link

```python
import doorstop

tree = doorstop.build()
for child in tree.find_document("TST"):
    if not child.links and child.text:
        # naive: link to same-numbered REQ
        parent_uid = f"REQ{str(child.uid.number).zfill(3)}"
        try:
            tree.link_items(child.uid, parent_uid)
        except doorstop.DoorstopError as exc:
            print(f"skip {child.uid}: {exc}")
```

### Validation with custom hooks

```python
#!/usr/bin/env python
import sys
from doorstop import build, DoorstopError, DoorstopInfo, DoorstopWarning

def check_document(document, tree):
    if sum(1 for i in document if i.normative) < 10:
        yield DoorstopInfo("fewer than 10 normative items")

def check_item(item, document, tree):
    if not item.attribute("type"):
        yield DoorstopWarning("no `type` attribute")
    if item.derived and not item.attribute("rationale"):
        yield DoorstopError("derived but no `rationale`")

def main():
    tree = build()
    ok = tree.validate(document_hook=check_document, item_hook=check_item)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Hook contracts:

- `document_hook(document, tree)` — yields `DoorstopInfo/Warning/Error`.
- `item_hook(item, document, tree)` — yields `DoorstopInfo/Warning/Error`.
- Any `DoorstopError` yielded makes `validate()` return `False`.

### Exporting / publishing programmatically

```python
from doorstop import build, exporter, publisher

tree = build()
req = tree.find_document("REQ")

# Export
exporter.export(req, "/tmp/req.xlsx", ext=".xlsx")
# Or stream lines
for line in exporter.export_lines(req, ext=".yml"):
    print(line)

# Publish
publisher.publish(req, "/tmp/req.html", ext=".html", linkify=True)
publisher.publish(tree, "/tmp/publish", ext=".html", index=True, matrix=True)
```

`publish()` signature: `publish(obj, path, ext=None, linkify=None, index=None,
matrix=None, template=None, toc=True, **kwargs)`. When `obj` is a `Tree`,
`path` is a directory; when it's a `Document`, `path` is a file.

### Importing programmatically

```python
from doorstop import build, importer

tree = build()
doc = tree.find_document("REQ")

# From an exported file
importer.import_file("/tmp/reqs.xlsx", doc, ext=".xlsx", mapping={"Requirement": "text"})

# Bootstrap a pre-existing directory as a Doorstop doc
doc = importer.create_document("SPEC", "./spec", parent="REQ")

# Backfill a specific item
item = importer.add_item("REQ", "REQ042", attrs={"text": "Legacy."})
```

## Exceptions

| Class | Path | When |
|---|---|---|
| `DoorstopError` | `doorstop.DoorstopError` | Invalid state, missing item/doc, cycle |
| `DoorstopWarning` | `doorstop.DoorstopWarning` | Validation warning |
| `DoorstopInfo` | `doorstop.DoorstopInfo` | Informational validation message |
| `DoorstopFileError` | `doorstop.common.DoorstopFileError` | Disk/format problems |

All inherit from `Exception`. The three validation severity classes are what
hooks yield; CLI severity flags (`-w`, `-e`) promote between them.

## Performance notes

- `tree.find_item` / `tree.find_document` cache by default. Mutating the disk
  outside the API can desynchronize the cache; in long scripts call
  `tree.load(reload=True)` after external changes.
- `tree.get_traceability()` is O(items × path-depth); don't call it in tight
  loops.
- Item save is atomic per-file but not transactional across items. If you
  abort mid-script, partial saves may remain.
