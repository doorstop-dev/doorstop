# Integrity Checks

To check a document hierarchy for consistency, run the main command:

```sh
$ doorstop
valid tree: REQ <- [ TST ]
```

## Links

To confirm that every item in a document links to its parents:

```sh
$ doorstop --strict-child-check
```
