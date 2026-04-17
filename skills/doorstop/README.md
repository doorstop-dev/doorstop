# Doorstop Skill

An Agent Skill that gives any compatible AI coding agent (Claude Code, Cursor,
Gemini CLI, Codex CLI, Antigravity) comprehensive, lazily-loaded knowledge of
the [Doorstop](https://github.com/doorstop-dev/doorstop) requirements-management
system.

## What it covers

- Every `doorstop` CLI subcommand and flag
- The Python API (`Tree`, `Document`, `Item`, `build`, `find_document`,
  `find_item`, `exporter`, `importer`, `publisher`) and its exception hierarchy
- `.doorstop.yml` and item YAML / Markdown-frontmatter schemas, including
  extended attributes, `attributes.reviewed`, `attributes.publish`, and
  `!include` composition
- End-to-end workflows: bootstrap, add/link/review/publish, CSV/XLSX round-trip,
  suspect-link resolution, release publishing
- The validation engine — full severity matrix and when each flag (`-L`, `-R`,
  `-C`, `-Z`, `-S`, `-W`, `-w`, `-e`) is safe
- The `doorstop-server` REST API
- Custom validators (`extensions.item_validator`), programmatic hooks, and
  `item_sha_required`
- A JSON snapshot script for agent loops and a CI-friendly lint wrapper

## Install

This skill uses the [OpenSkills](https://github.com/numman-ali/openskills)
universal installer so one package works across Claude Code, Cursor, Gemini
CLI, Codex CLI, and Antigravity.

```sh
# Install from a published GitHub repo, project-local (./.claude/skills/doorstop)
npx openskills install doorstop-dev/doorstop

# Install globally (~/.claude/skills/doorstop)
npx openskills install doorstop-dev/doorstop --global

# Install from a local checkout while developing this skill
npx openskills install ./skills/doorstop --global
```

After install, agents automatically discover the skill via its description in
`SKILL.md` — no further wiring required.

> **Note on `npx skills add`**: some docs use the shorthand `npx skills add …`;
> in April 2026 the working command is `npx openskills install …`. If an alias
> is added to `openskills` later, both forms will work.

## Layout

```
skills/doorstop/
├── SKILL.md                      # entry point (always-on description, lean body)
├── README.md                     # this file
├── references/                   # lazy-loaded deep references
│   ├── cli-commands.md
│   ├── python-api.md
│   ├── file-formats.md
│   ├── workflows.md
│   ├── validation.md
│   ├── publishing.md
│   ├── import-export.md
│   ├── server-api.md
│   ├── extensions.md
│   └── troubleshooting.md
├── scripts/
│   ├── doorstop_snapshot.py      # JSON snapshot for agents
│   └── doorstop_lint.sh          # CI-friendly validation
└── assets/
    └── example_reqs/             # tiny two-document example tree
```

## Design

This skill follows the **Thin Harness, Fat Skills** principle:

- The always-on surface (SKILL.md frontmatter) is compact.
- Domain judgment lives in `references/*.md`, loaded only when the task needs
  it.
- Deterministic truth (flag tables, schemas, REST routes) is expressed as
  tables and example files — never as unbounded prose.
- The skill never tries to control harness runtime (scheduling, tool
  orchestration). It describes *what* to do; the harness decides *how*.

## Requirements

- Python 3.9+ with Doorstop installed (`pip install doorstop`)
- `git` (Doorstop requires a VCS root)
- Optional: `openpyxl` for XLSX round-trip (installed automatically with
  Doorstop), `bottle` for the REST server (same)

## Contributing

This skill lives inside the `doorstop` source repository so it versions with the
tool itself. When Doorstop's CLI surface, file format, or Python API changes,
update the matching reference in `references/` in the same PR.
