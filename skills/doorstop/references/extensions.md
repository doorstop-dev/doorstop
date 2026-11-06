# Extensions

Three extension points, from least to most invasive:

1. **`extensions.item_validator`** in `.doorstop.yml` — per-document custom
   validator loaded from a Python file alongside the document.
2. **`tree.validate(document_hook=, item_hook=)`** from a Python script
   that runs in place of `doorstop`.
3. **Custom publisher / custom attribute** — subclass into
   `doorstop.core.publishers` or read extended attributes via the Python
   API.

Plus one opt-in flag for reference integrity: **`item_sha_required`**.

## `extensions.item_validator` — per-document validator

Enable in a document's `.doorstop.yml`:

```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
extensions:
  item_validator: validators/req_validator.py   # path relative to .doorstop.yml
```

Create the Python file (here `reqs/req/validators/req_validator.py`):

```python
from doorstop import DoorstopError, DoorstopInfo, DoorstopWarning


def item_validator(item):
    """Yield Doorstop{Error,Warning,Info} for each issue."""
    if not item.get("owner"):
        yield DoorstopWarning("no owner assigned")
    if item.derived and not item.get("rationale"):
        yield DoorstopError("derived item without rationale")
    if item.active and not item.get("type"):
        yield DoorstopInfo("no type tag")
```

Rules:

- The function **must** be named `item_validator` and take a single `item`
  argument.
- It may `yield` or `return` an iterable. Yielding is idiomatic.
- Yield `DoorstopInfo`, `DoorstopWarning`, or `DoorstopError` — severity
  maps 1:1 to the validation severity matrix (see `validation.md`).
- Errors short-circuit the item's validation exit status; warnings and infos
  don't.
- The validator runs on **every** item in the document, every time
  `doorstop` (or `tree.validate()`) runs.
- The validator is loaded via `importlib` from the path in `.doorstop.yml`.
  Keep it free of heavy imports — no network, no DB.
- Path is relative to `.doorstop.yml`. Absolute paths and `!include` are not
  supported here.

Use cases:

- Enforce required extended attributes (`owner`, `type`,
  `verification-method`).
- Enforce ref-file SHA integrity (the canonical example — see
  `item_sha_required` below).
- Enforce text-style rules ("shall" vocabulary, length limits).
- Cross-check links against an external source (sparingly — hits disk every
  validation).

## `item_sha_required` — reference-file integrity

Opt in per-document:

```yaml
extensions:
  item_sha_required: true
```

With this flag:

- Every entry in an item's `references:` list must carry a `sha:` field
  (SHA-256 of the referenced file's contents).
- On `doorstop review <item>`, doorstop computes and inserts the `sha:` if
  missing.
- When a referenced file changes on disk, its SHA won't match the stored
  value → the item is suspect in a way that isn't caught by the default
  fingerprint. Pair with a custom `item_validator` to turn the mismatch
  into a `DoorstopError` (`docs/api/scripting.md:100-107`):

```python
from doorstop import DoorstopError

def item_validator(item):
    if getattr(item, "references", None) is None:
        return
    for ref in item.references:
        if ref.get("sha") != item._hash_reference(ref["path"]):
            yield DoorstopError("referenced file changed without re-review")
```

## `tree.validate(document_hook=, item_hook=)` — programmatic validator

Replace `doorstop` (the CLI) with a Python script for cases where
`item_validator` isn't enough (cross-document logic, shared state, expensive
setup you want done once):

```python
#!/usr/bin/env python
import sys

from doorstop import build, DoorstopError, DoorstopInfo, DoorstopWarning


def main():
    tree = build()
    ok = tree.validate(document_hook=check_document, item_hook=check_item)
    sys.exit(0 if ok else 1)


def check_document(document, tree):
    normative_count = sum(1 for i in document if i.normative)
    if normative_count < 10:
        yield DoorstopInfo(f"{document}: only {normative_count} normative items")


def check_item(item, document, tree):
    if not item.get("type"):
        yield DoorstopWarning(f"{item.uid}: no type tag")
    if item.derived and not item.get("rationale"):
        yield DoorstopError(f"{item.uid}: derived but no rationale")


if __name__ == "__main__":
    main()
```

Source: `docs/api/scripting.md:39-71`.

Hook signatures:

- `document_hook(document, tree)` — called once per document.
- `item_hook(item, document, tree)` — called once per item.

Both are generators. Both are optional; pass only the ones you need.

Exit: `tree.validate()` returns `True` on success (no errors), `False`
otherwise. Your script chooses how to map that to an exit code.

## Custom publisher

Built-in publishers live in `doorstop/core/publishers/` (text, markdown,
html, latex). To add a new format:

1. Subclass `BasePublisher` from `doorstop/core/publishers/base.py`.
2. Register it by importing and invoking it directly — the CLI's `publish`
   subcommand only knows about the built-in formats. For one-off use, call
   from a script:

```python
import doorstop
from my_pkg.publishers import ReqIFPublisher

tree = doorstop.build()
ReqIFPublisher().publish(tree, "/tmp/out.reqif")
```

The CLI `publish` subcommand is not pluggable without forking doorstop or
patching `doorstop.core.publisher`. Keep custom publishers in a sibling
package and drive them from a script for maintainability.

## Custom attributes (reminder)

Extended attributes are first-class via the Python API — no extension
needed. See `file-formats.md` for `attributes.defaults`,
`attributes.reviewed`, and `attributes.publish`. Common uses: `owner`,
`priority`, `ticket`, `type`, `verification-method`.

To enforce them, combine:

- `attributes.defaults` (so items without the attr still have a value)
- `attributes.reviewed` (so changes feed the fingerprint)
- `extensions.item_validator` (to raise errors on bad values)

## Non-negotiables for extensions

- **Don't mutate items from a validator.** Validators run during
  `tree.validate()` — mutations during validation are undefined behavior
  and won't be re-checked.
- **Don't raise exceptions** from a validator. Yield `DoorstopError`
  instead. Uncaught exceptions abort the entire validation run.
- **Keep validators idempotent and pure.** The same item should always
  yield the same set of issues.
- **Don't rely on ordering** between `document_hook` and `item_hook`
  invocations — order is an implementation detail.

## Debugging a validator

If a validator isn't running:

1. Confirm the path in `.doorstop.yml` is correct relative to the
   `.doorstop.yml` file (not to the project root).
2. Confirm the function is named `item_validator` exactly.
3. Run `doorstop -v` to surface import errors from the validator file.
4. Add a `print` at the top of `item_validator` to confirm it's loaded.
