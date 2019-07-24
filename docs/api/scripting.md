<h1>Scripting Interface</h1>

Being written in Python, Doorstop allows you to leverage the full power of Python to write scripts to manipulate requirements, run custom queries across all documents, and even inject your own validation rules.

# REPL

For ad hoc introspection, let Doorstop build your tree of documents in your preferred Python [REPL](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop) or notebook session:

```python
>>> import doorstop
>>> tree = doorstop.build()
>>> tree
<Tree REQ <- [ TUT <- [ HLT ], LLT ]>
>>> len(tree.documents)
4
>>> document = tree.find_document('REQ')
>>> document
Document('/Users/Browning/Documents/doorstop/reqs')
>>> sum(1 for item in document if item.active)
18
```

# Generic Scripting

For reusable workflows, create a Python script that acts on your tree of documents:

```python
#!/usr/bin/env python

import doorstop

tree = doorstop.build()
document = tree.find_document('REQ')
count = sum(1 for item in document if item.active)

print(f"{count} active items in {document}")
```

# Validation Hooks

To extend the default set of [validations](../cli/validation.md) that can be performed, Doorstop provides a "hook" mechanism to simplify scripts that need to operate on multiple documents or items.

For this use case, create a script to call in place of the default command-line interface:

```python
#!/usr/bin/env python


import sys
from doorstop import build, DoorstopInfo, DoorstopWarning, DoorstopError


def main():
    tree = build()
    success = tree.validate(document_hook=check_document, item_hook=check_item)
    sys.exit(0 if success else 1)


def check_document(document):
    if sum(1 for i in document if i.normative) < 10:
        yield DoorstopInfo("fewer than 10 normative items")


def check_item(item):
    if not item.get('type'):
        yield DoorstopWarning("no type specified")
    if item.derived and not item.get('rationale'):
        yield DoorstopError("derived but no rationale")


if __name__ == '__main__':
    main()
```

Both `document_hook` and `item_hook` are optional, but if provided these callbacks will be passed each corresponding instance. Each callback should yield instances of Doorstop's exception classes based on severity of the issue.
