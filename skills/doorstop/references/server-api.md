# Server / REST API

The `doorstop-server` is a Bottle app that exposes the tree over HTTP. Two
purposes:

1. **Human**: browse the tree in a browser with per-item HTML views and a
   traceability matrix.
2. **Agent**: safely reserve item numbers across concurrent clients via
   `POST /documents/<prefix>/numbers`, and read JSON views of documents and
   items.

Source: `doorstop/server/main.py`.

## Start the server

```sh
doorstop-server                              # defaults to 127.0.0.1:7867
doorstop-server -P 8080                      # custom port
doorstop-server -H 0.0.0.0 -P 7867           # bind all interfaces
doorstop-server -j /path/to/project          # alternate project root
doorstop-server --launch                     # open browser automatically
doorstop-server --debug                      # verbose, auto-reload on code change
doorstop-server --wsgi -b /doorstop          # when hosted behind a reverse proxy
```

Source: `doorstop/server/main.py:32-89`.

Defaults:

| Option | Default | Override |
|---|---|---|
| Host | `127.0.0.1` | `-H` / `--host` |
| Port | `7867` | `-P` / `--port` |
| Project root | Auto-detected via `vcs.find_root` | `-j` / `--project` |
| Base URL | `""` | `-b` / `--baseurl` (WSGI) |

## Content negotiation

Every JSON-capable endpoint returns HTML by default. To receive JSON, send
`Accept: application/json` (handled by `utilities.json_response`).

```sh
curl http://127.0.0.1:7867/documents \
  -H "Accept: application/json"
```

## Endpoints

### GET `/` and `/index`

HTML only. Renders the tree index page.

### GET `/traceability`

- HTML: traceability matrix page.
- JSON: `{"traceability": [["REQ001", "LLR003", "TST010"], ...]}` — rows are
  link chains across the tree; items are stringified UIDs.

### GET `/documents`

- HTML: per-document links.
- JSON: `{"prefixes": ["REQ", "LLR", "TST"]}`.

### GET `/documents/all`

- JSON only (HTML falls back to the `/documents` list page).
- Body: `{"REQ": {"REQ001": {...item data...}, "REQ002": {...}}, "LLR": {...}}`.

Dumps every item in every document as a single JSON blob. Useful for a
full-tree snapshot.

### GET `/documents/<prefix>`

- HTML: doorstop-rendered document page with a TOC and linkified UIDs.
- JSON: `{"REQ001": {...item data...}, "REQ002": {...}}` — same shape as
  `/documents/all`, scoped to one prefix.

### GET `/documents/<prefix>/items`

- JSON: `{"uids": ["REQ001", "REQ002", ...]}`.

### GET `/documents/<prefix>/items/<uid>`

- HTML: item page.
- JSON: `{"data": {...item data...}}`.

### GET `/documents/<prefix>/items/<uid>/attrs`

- JSON: `{"attrs": ["active", "derived", "level", ...]}` — sorted attribute
  names.

### GET `/documents/<prefix>/items/<uid>/attrs/<name>`

- JSON: `{"value": <whatever>}` — raw attribute value (string, bool, list,
  dict, or null).

### POST `/documents/<prefix>/numbers`

**The one mutating endpoint.** Reserves and returns the next item number
for `<prefix>`:

- JSON: `{"next": 17}`.
- Plain text fallback: `17`.

The server tracks `numbers[prefix]` in memory and also honors the on-disk
`next_number` computed from the current tree. When the CLI (`doorstop add
<prefix>`) runs with `--server`, it calls this endpoint to reserve a UID
atomically.

### GET `/template/<filename>`

Serves built-in HTML template assets (CSS, JS). 404 if not found.

### GET `/documents/assets/<filename>`

Serves document-level assets (images embedded in requirement texts).
Searches every document's `assets/` folder.

## How the CLI uses the server

When the server is running and reachable, these CLI commands will:

- `doorstop add <prefix>` — reserve a UID via `POST
  /documents/<prefix>/numbers`. Prevents two concurrent shells from
  reserving the same number.

When the server is unreachable or `-f/--force` is set, the CLI falls back
to local number counting. In that case, concurrent writers can collide.

Flags affecting server behavior on the client side:

- `--server HOST` — hostname (default from `settings.SERVER_HOST`).
- `--port NUMBER` — port (default from `settings.SERVER_PORT` = 7867).
- `-f/--force` — bypass the server entirely.

## Agent patterns

**Read the tree without parsing CLI output**:

```sh
curl -s -H "Accept: application/json" \
  http://127.0.0.1:7867/documents/all > /tmp/tree.json
```

**Get one item's attrs for decision-making**:

```sh
curl -s -H "Accept: application/json" \
  http://127.0.0.1:7867/documents/REQ/items/REQ001
```

**Reserve a UID before creating an item out-of-band** (rare — prefer
`doorstop add`):

```sh
curl -s -X POST -H "Accept: application/json" \
  http://127.0.0.1:7867/documents/REQ/numbers
# {"next": 18}
```

## CORS

`Access-Control-Allow-Origin: *` is set on every response
(`server/main.py:154`). This is convenient for local tooling; if you
expose the server beyond localhost, put it behind an authenticated proxy.

## WSGI deployment

```sh
doorstop-server --wsgi -b /doorstop
```

The `-b` flag tells Bottle the base URL the proxy forwards under, so
generated links and static-asset paths are correct.

## What the server does **not** do

- No PATCH/PUT/DELETE — item mutations must go through the CLI or Python
  API. The REST surface is read-mostly with a single POST to reserve
  numbers.
- No authentication or TLS. Don't expose this directly on the public
  internet.
- No live-reload of the tree. If you edit files on disk, restart the
  server (or run with `--debug` which auto-reloads on file change).

## Related

- For atomic UID reservation semantics from the CLI side, see
  `cli-commands.md` under `add`.
- For the Python API equivalent of "inspect everything", use
  `doorstop.build()` and iterate — no server required.
  (See `python-api.md`.)
