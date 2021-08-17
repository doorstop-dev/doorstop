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

Mark an unreviewed item, document, or all documents as reviewed:

- `doorstop review REQ-001    # Marks item REQ-001 as reviewed`
- `doorstop review REQ        # Marks all items in document REQ as reviewed`
- `doorstop review all        # Marks all documents as reviewed`

Mark suspect links in an item, document, or all documents, as cleared:

- `doorstop clear LLR-001         # Marks all links originating in item LLR-001 as cleared`
- `doorstop clear LLR-001 REQ     # Marks links in item LLR-001 to document REQ as cleared`
- `doorstop clear LLR REQ         # Marks all links from LLR that target REQ as cleared`
- `doorstop clear LLR all         # Marks all links originating in document LLR as cleared`
- `doorstop clear all             # Marks all links in all documents as cleared`

Create an HTML document in `publish`:

- `doorstop publish all ./publish`

View in the graphical user interface (GUI):

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
