# Example reqs tree

A minimal two-document doorstop tree:

- `reqs/` — root document, prefix `REQ`
  - `REQ001` — heading ("System Requirements"), level 1.0
  - `REQ002` — normative requirement ("Boot time"), level 1.1
- `tests/` — child document, prefix `TST`, parent `REQ`
  - `TST001` — normative test linked to `REQ002`

Use it as:

- A copy-paste starting template for a new project.
- Ground truth for the canonical on-disk shape (see
  `references/file-formats.md`).
- A target for skill verification — `doorstop` from the root should exit 0
  (with INFO about unreviewed items until you run `doorstop review all`).

## Try it

```sh
# Copy into a fresh git repo:
mkdir /tmp/demo && cd /tmp/demo && git init
cp -r /path/to/skills/doorstop/assets/example_reqs/. .
doorstop                                # validate (INFO: unreviewed)
doorstop review all                     # stamp everything
doorstop                                # clean
doorstop publish all ./publish          # HTML output
```
