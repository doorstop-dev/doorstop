# Troubleshooting

Decision tree for the most common failure modes. Each entry: symptom,
diagnosis, exact commands to run.

## `doorstop` exits with "no tree found" / "no documents found"

**Symptom**: `doorstop` prints `ERROR: no documents found` or exits
immediately.

**Diagnosis**: Either you're outside a VCS root, or no `.doorstop.yml`
exists under the cwd.

```sh
git rev-parse --show-toplevel        # should print repo root
find . -name ".doorstop.yml"         # should list at least one
```

**Fix**:

- Outside VCS → `cd` into the repo, or `git init` if genuinely bootstrapping.
- No `.doorstop.yml` anywhere → this is a fresh tree; run `doorstop create
  <PREFIX> <PATH>` (see `workflows.md#bootstrap`).

## "invalid item filename"

**Symptom**: `DoorstopError: invalid item filename: foo.yml`.

**Diagnosis**: A file in the document directory has a name that doesn't
parse as a UID under the document's `prefix` / `sep` / `digits` settings.
Common causes: stray files, renamed items, importing a spreadsheet that
stripped leading zeros.

**Fix**:

```sh
ls reqs/req/                          # find offending file(s)
```

- If it's a stray file (README, `.gitkeep`) → move it out of the document
  directory.
- If it's a valid requirement with a broken filename → rename it to a
  correct UID (preserving the number), or `doorstop remove` + `doorstop
  add` to regenerate.

## Item is flagged "unreviewed" after a tiny edit

**Symptom**: `WARNING: REQ: REQ002: unreviewed changes` after you only
changed `header:` or `level:`.

**Diagnosis**: Not the usual case. `header` and `level` don't feed the
fingerprint (see `validation.md#fingerprint-and-suspect-links`). Check
whether an extended attribute that is listed in `attributes.reviewed` also
changed.

**Fix**:

```sh
git diff reqs/req/REQ002.yml
grep -A5 "^attributes" reqs/req/.doorstop.yml
```

If the diff shows text/ref/references/links changed, `doorstop review
REQ002`. If only `header`/`level` changed, look harder at
`attributes.reviewed` for an extended attr you forgot you listed.

## Suspect links after parent edit

**Symptom**:

```
WARNING: LLR: LLR003: suspect link: REQ002
WARNING: LLR: LLR004: suspect link: REQ002
```

**Diagnosis**: Normal. Parent content changed; children stored the old
parent fingerprint. See `workflows.md` recipe 4.

**Fix** in this order:

```sh
doorstop review REQ002                # accept the parent edit
# Then for each suspect child, either:
doorstop clear LLR003                 # accept parent change, no child edit
# or:
$EDITOR reqs/llr/LLR003.yml
doorstop review LLR003                # stamp the child content change
```

**Do not** `doorstop clear` without reviewing the parent first. That stamps
the children with the old parent's fingerprint, which then won't flag as
suspect on the next change — you'll miss a real regression.

## Cycle detected

**Symptom**: `WARNING: ...: detected a cycle with a back edge from REQ002
to LLR003`.

**Diagnosis**: A link path forms a cycle (A → B → ... → A). Doorstop's
`CycleTracker` (DFS) reports it.

**Fix**:

```sh
doorstop                              # see the full cycle
doorstop unlink LLR003 REQ002         # pick an edge and remove it
```

The right edge to cut is the one that shouldn't exist semantically. If you
can't tell, ask whoever authored the tree.

## Unresolved external reference

**Symptom**: `ERROR: REQ: REQ010: external reference not found:
src/sensors/temp.c`.

**Diagnosis**: `ref:` or `references:` points to a file or keyword that
doesn't exist in the project tree.

**Fix**:

```sh
grep -rn "src/sensors/temp.c"         # did the file move?
```

- File moved → `doorstop edit REQ010` and update `references:` path.
- File deleted legitimately → `doorstop edit REQ010` and remove the ref.
- File exists but outside the checkout (e.g., only in a submodule not
  cloned) → either clone it, or run with `-R/--no-ref-check` for that
  session (don't ship it).

## "multiple root documents" on `doorstop`

**Symptom**: `ERROR: multiple root documents: ...` listing two or more
document directories (often with the same prefix).

**Diagnosis**: Doorstop walks the VCS root (by default) and picks up every
`.doorstop.yml` it finds. If your repo contains a second, unrelated
Doorstop tree — a vendored example, a teaching fixture, a submodule, a
test asset — both roots get merged into the same tree and clash.

**Fix**: Drop a `.doorstop.skip-all` marker at the top of the subtree you
want excluded. The file's contents are ignored; only its presence matters.

```sh
touch path/to/unrelated/doorstop/tree/.doorstop.skip-all
doorstop                              # rescans — the subtree is pruned
```

The marker is recognized by `doorstop/core/builder.py`: when `os.walk`
visits a directory containing a `.doorstop.skip-all` file, that directory
and everything beneath it are removed from discovery.

This is the same mechanism the skill itself uses: see
`skills/doorstop/assets/.doorstop.skip-all` — it keeps the bundled
`example_reqs/` tree from colliding with Doorstop's own requirements when
this skill lives inside a repo that is itself a Doorstop project.

## "document already exists" on `doorstop create`

**Symptom**: Create fails even though the path looks empty.

**Diagnosis**: Either a stray `.doorstop.yml` exists at the target path,
or another document in the tree already claims that prefix.

**Fix**:

```sh
find . -name ".doorstop.yml" -exec grep -l "prefix: REQ" {} +
```

- If the prefix is taken elsewhere → choose a different prefix.
- If a stale `.doorstop.yml` lingers → `doorstop delete <PREFIX>` (safer)
  or remove the file manually and retry.

## "items numbered out of order" after parallel edits

**Symptom**: Two agents ran `doorstop add REQ` concurrently and collided on
UIDs.

**Diagnosis**: Number reservation wasn't atomic because no server was
running (or `-f/--force` was passed).

**Fix**:

```sh
doorstop-server &                    # background the server
doorstop add REQ -T "..."            # subsequent adds reserve atomically
```

For existing collisions: `git reset --hard` back to before the collision
and replay the adds sequentially.

## Levels skipped or duplicated

**Symptom**:

```
INFO: REQ: REQ005: skipped level 1.3
WARNING: REQ: REQ006 and REQ007 both at level 1.4
```

**Fix**:

- Skipped (INFO) → cosmetic, optional. Run `doorstop -r` to re-pack levels
  (writes to disk).
- Duplicate (WARNING) → `doorstop edit <uid>` on one item and change
  `level`, or `doorstop reorder <PREFIX>` for an interactive pack.

## UID prefix no longer matches document prefix

**Symptom**: `INFO: UID REQ001: UID prefix is not equal to document prefix
REQ-V2`.

**Diagnosis**: Someone edited `.doorstop.yml` to change `prefix:` after
items were created. Don't do this.

**Fix**:

- Revert the `.doorstop.yml` change: `git checkout --
  reqs/req/.doorstop.yml`.
- If the rename was intentional: delete the document
  (`doorstop delete REQ`) and import as a new one, or use
  `doorstop import` with the new prefix. Expect a full re-link pass.

## Publish artifact looks wrong / missing items

**Symptom**: `publish/index.html` is missing items, or levels are jumbled.

**Diagnosis**: Either pre-publish validation wasn't clean, or `active:
false` items are being omitted (this is correct behavior; they're hidden).

**Fix**:

```sh
doorstop                              # confirm tree is clean
grep -rh "^active:" reqs/ | sort -u   # are unexpected items inactive?
```

Publish again after the tree validates clean. To include inactive items in
publish, set them `active: true`.

## `doorstop review` did nothing / `reviewed:` stamp still null

**Symptom**: After `doorstop review REQ001`, the item still shows
`reviewed: null` and the warning persists.

**Diagnosis**: Rare. Usually the item file is read-only or the process was
run without write access to the project root.

**Fix**:

```sh
ls -l reqs/req/REQ001.yml
doorstop review REQ001 -v            # verbose run to see errors
```

Check file perms, disk space, and that the cwd isn't inside a read-only
overlay filesystem.

## Server won't start / port in use

**Symptom**: `doorstop-server` exits with `OSError: [Errno 48] Address
already in use`.

**Fix**:

```sh
lsof -i :7867                         # find the offender
doorstop-server -P 7868               # use a different port
```

If agents are configured to talk to the default port, either kill the old
server or pass `--port 7868` to clients.

## Import from XLSX dropped leading zeros on UIDs

**Symptom**: After round-trip through Excel, items are named `REQ1` instead
of `REQ001`. Doorstop may treat them as new items.

**Fix**: Format the UID column as **text** in Excel *before* editing. If
already corrupted:

```sh
git checkout -- reqs/req/              # revert
```

Then re-export, re-format, re-import.

## I edited `reviewed:` by hand and everything broke

**Symptom**: Every item shows unreviewed or suspect, even ones you didn't
touch.

**Fix**:

```sh
git checkout -- reqs/
```

Never edit `reviewed:` manually. The stamp is SHA-256 over a specific
canonical representation and will not match anything you type. Use
`doorstop review`.

## Validator throws an exception

**Symptom**: `doorstop` aborts with a traceback pointing into your
`item_validator.py`.

**Diagnosis**: Validators must yield `DoorstopError` (or friends), not
raise.

**Fix**: Wrap risky operations in try/except inside the validator, and
`yield DoorstopError(str(exc))` instead of letting the exception propagate.
See `extensions.md` for signature rules.

## Tree `validate()` returns False but no issues printed

**Symptom**: CLI says "command failed" but you don't see WARNING/ERROR
lines.

**Diagnosis**: You're at the default verbosity. INFO lines are hidden, but
an unresolved internal error can still set the exit status.

**Fix**:

```sh
doorstop -v                           # INFO visible
doorstop -vv                          # DEBUG visible
```

## When to reach for `scripts/doorstop_snapshot.py`

If any of the above needs a structured view that's hard to extract from
CLI stdout:

```sh
python skills/doorstop/scripts/doorstop_snapshot.py > /tmp/tree.json
jq '.documents.REQ.items.REQ002' /tmp/tree.json
```

The snapshot captures every item's attributes, links, and the validation
issues, all as JSON.
