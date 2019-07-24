# Plain Text

Individual documents can be displayed:

```sh
$ doorstop publish TST
```

# HTML

The collection of documents can be published as a webpage:

```sh
$ doorstop publish all ./dist/
```

# Additional formats

Or a file can be created using one of the supported extensions:

```sh
$ doorstop publish TST path/to/tst.md
publishing TST to path/to/tst.md...
```

Supported formats:

- Text: `.txt`
- Markdown: `.md`
- HTML: `.html`
