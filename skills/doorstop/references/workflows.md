# Workflows

End-to-end recipes for the common tasks. Each recipe lists the commands in
order, the expected output, and checkpoints where you should pause and
validate before continuing.

For flag details, see `cli-commands.md`. For file-format details, see
`file-formats.md`. For validation semantics, see `validation.md`.

## 1. Bootstrap a new project

**Precondition**: you're in a git repo (or `git init` before starting).
Doorstop refuses to run outside a VCS root.

```sh
git init                                    # if the repo is fresh
doorstop create REQ ./reqs/req              # root document, no parent
doorstop add REQ -T "System shall boot within 5 seconds"
doorstop create LLR ./reqs/llr --parent REQ # child document
doorstop add LLR -T "Bootloader shall finish in ≤ 2 s"
doorstop link LLR001 REQ001                 # child → parent
doorstop                                     # validate
```

Checkpoints:

- After `create`: a `reqs/req/.doorstop.yml` exists with `prefix: REQ`.
- After `add`: an item file `REQ001.yml` exists. No review yet (`reviewed:
  null`) — expected INFO.
- After `link`: `LLR001.yml` has a `links: [{REQ001: null}]` entry.
- After `doorstop`: tree renders, no WARNING/ERROR. Unreviewed items show as
  INFO (visible with `-v`).

First-time commit:

```sh
git add reqs/
git commit -m "bootstrap doorstop tree"
```

## 2. Add an item and review it

```sh
doorstop add REQ -T "REQ005: power-off within 1 s when lid closes"
$EDITOR reqs/req/REQ005.yml                  # optional — refine text/level
doorstop                                     # verify the edit
doorstop review REQ005
```

After `review`, `REQ005.yml` will have a non-null `reviewed:` stamp. Commit.

### Reserve a batch of UIDs atomically

When you know you need N items, don't loop — let `add` reserve them through
the server (or the local counter, if no server is running):

```sh
doorstop add REQ -c 5                        # creates REQ00N..REQ00N+4
```

This is safer under concurrent agent runs because number reservation is
atomic at the server (`POST /documents/<prefix>/numbers`, see
`server-api.md`).

## 3. Link items across documents

```sh
doorstop link TST010 REQ002                  # TST010 declares REQ002 as parent
```

Linking direction is always child → parent. After linking, the child's
`links:` gains `{REQ002: <parent-fingerprint>}`. To remove: `doorstop unlink
TST010 REQ002`.

If you renamed a requirement (delete + re-add under a new UID), every child
that pointed to the old UID must be re-linked. There's no rename operation.

## 4. Edit content, then bring reviews and suspect links back in line

Scenario: you changed `REQ002.text`. Expected cascade:

```sh
$EDITOR reqs/req/REQ002.yml
doorstop                                     # see warnings
```

You'll see:

- `WARNING: REQ: REQ002: unreviewed changes`
- `WARNING: LLR: LLR003: suspect link: REQ002`   (for every child)

Resolve in this order:

```sh
doorstop review REQ002                       # accept the parent edit
doorstop                                     # parent is now clean
                                              # children still show suspect
# For each child, choose:
doorstop clear LLR003                        # accept parent change, no child edits
#   — OR —
$EDITOR reqs/llr/LLR003.yml                  # edit the child text
doorstop review LLR003                       # stamp child (also refreshes link stamps)
```

Do **not** invert this order. If you `clear` children before reviewing the
parent, the link stamps will record an intermediate fingerprint and the next
round of parent edits won't flag them as suspect when they should.

## 5. Publish a release snapshot

```sh
doorstop                                     # MUST exit 0
doorstop publish all ./publish
```

Layout under `./publish`:

```
publish/
├── index.html                    # tree TOC across all documents
├── REQ.html
├── LLR.html
├── TST.html
└── traceability.csv              # if --traceability passed
```

Single-document publish:

```sh
doorstop publish REQ ./publish/REQ.html      # explicit extension drives format
doorstop publish REQ ./publish/REQ.md
doorstop publish REQ ./publish/REQ.tex
doorstop publish REQ ./publish/REQ.txt
```

See `publishing.md` for templates, `--no-levels`, `--no-child-links`,
traceability, and linkifying.

## 6. Round-trip via spreadsheet

```sh
doorstop export REQ /tmp/req.xlsx            # export
# Edit /tmp/req.xlsx in Excel/LibreOffice. Leave UID blank for new items.
doorstop import /tmp/req.xlsx REQ            # import back
doorstop                                     # validate — expect unreviewed
```

New items (blank UID column) get freshly-reserved UIDs. Modified items keep
their UIDs but land as **unreviewed**. Run `doorstop review` on each, or do
a bulk review from the API (see `python-api.md`).

See `import-export.md` for CSV/TSV, column mapping (`-m/--map`), and the
explicit `create` form (`doorstop import --item REQ REQ042 -a level=1.5`).

## 7. Bulk changes from Python

When a restructure needs more than a few commands, script it:

```python
import doorstop

tree = doorstop.build(".")
req = tree.find_document("REQ")
for item in req:
    if item.get("type") == "deprecated":
        item.set("active", False)
        item.save()
doorstop.publisher.publish(tree, "./publish", "html")
```

Always run `doorstop` after the script to confirm the tree is still valid,
then review any items the script touched. Script changes bypass the
`doorstop edit` wrapper, so they will *not* be auto-reviewed.

## 8. Promote a document to have a parent

You cannot edit `parent:` once items exist under the document — it isn't
truly read-only on disk, but child link checks against the old tree
structure will silently diverge. Safe path:

1. Create a new sibling document with the correct parent.
2. `doorstop export OLD /tmp/old.xlsx` and import into the new doc.
3. `doorstop delete OLD` once everything is migrated and links are
   re-pointed.

## 9. CI gate recipe

```sh
# scripts/doorstop_lint.sh (shipped with this skill)
doorstop -e -Z                               # errors on warnings, strict children
```

Exit 0 → green. Non-zero → fail the build. Pair with:

```yaml
# .github/workflows/requirements.yml — illustrative
- run: pip install doorstop
- run: ./skills/doorstop/scripts/doorstop_lint.sh
```

## 10. Restore after destructive mistakes

Doorstop state is git-backed. If something went wrong (accidental `delete`,
stray `review`, borked import):

```sh
git status reqs/
git diff reqs/
git checkout -- reqs/                       # revert everything
# or, surgically:
git checkout -- reqs/req/REQ005.yml
```

This is why **commit after every logical batch of changes**. Uncommitted
doorstop state is nearly meaningless — it can't be reproduced, reviewed in a
PR, or rolled back cleanly.

## Checkpoints every workflow should hit

Before declaring done:

- `doorstop` exits 0 (or with only accepted INFO).
- Every item you edited has been passed through `doorstop review`.
- If you published, the publish directory exists and the artifact loads.
- Changes are staged or committed.
