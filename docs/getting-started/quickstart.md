<h1> Quickstart </h1>

Help with Doorstop:

- `doorstop --help`
- `doorstop <COMMAND> --help`

Set up a repository for controlling documents:

- `mkdir /path/to/docs`
- `cd /path/to/docs`
- `git init`

Create a root parent requirements document:

- `doorstop create REQ ./reqs/req`

Add items to a document, will be automatically numbered:

- `doorstop add REQ`

Create a child document (low level requirements) to link to the parent:

- `doorstop create LLR ./reqs/llr --parent REQ`
- `doorstop add LLR`

Link low level items to requirements (separators like '-' are optional and ignored):

- `doorstop link LLR001 REQ001`

Check integrity of the document tree and validate links:

- `doorstop`

Create an HTML document in `publish`:

- `doorstop publish all ./publish`

View in the GUI:

- `doorstop-gui`

Browse the doc tree on a local web server:

- `doorstop-server`
- Point browser to: http://127.0.0.1:7867/
- Ctrl+C to quit the server.

Round-trip to Excel:

- `doorstop export -x REQ REQ.xslx`
- Make edits in Excel. Do not edit UIDs. Leave UID cells blank for new items.
- `doorstop import REQ.xslx REQ`
- `rm REQ.xlsx`
