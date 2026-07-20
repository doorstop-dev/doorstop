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

## Why the parent directory has `.doorstop.skip-all`

The sibling `skills/doorstop/assets/.doorstop.skip-all` marker tells
doorstop not to descend into this directory when scanning a VCS root. That
matters when the skill is installed inside a repo that is *itself* a
Doorstop project — without the marker, doorstop would try to merge this
example tree into the host project's tree and fail with "multiple root
documents".

The marker lives one level **above** this directory, so it stays behind
when you copy this tree elsewhere.

## Try it

```sh
# Copy into a fresh git repo:
mkdir /tmp/demo && cd /tmp/demo && git init
cp -r /path/to/skills/doorstop/assets/example_reqs/. .
doorstop                                # validate (INFO: unreviewed)
doorstop review all                     # stamp everything
doorstop                                # clean
doorstop publish REQ ./REQ.md           # single-doc Markdown publish
```

Note the trailing `/.` in the `cp` above — copies the contents, not the
directory itself.
