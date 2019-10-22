## Editor

Doorstop will open files using the editor specified by the `$EDITOR` environment variable. If that is unset, it will attempt to open files in the default editor for each file type.

## Git

**Linux / macOS**

No additional configuration should be necessary.

**Windows**

Windows deals with line-endings differently to most systems, favoring `CRLF` (`\r\n`) over the more traditional `LF` (`\n`).
The `YAML` files saved and revision-controlled by Doorstop have `LF`
line-endings, which can cause the following warnings:

```
(doorstop) C:\temp\doorstop>doorstop reorder --auto TS
building tree...
reordering document TS...
warning: LF will be replaced by CRLF in tests/sys/TS003.yml.
The file will have its original line endings in your working directory.
warning: LF will be replaced by CRLF in tests/sys/TS001.yml.
The file will have its original line endings in your working directory.
warning: LF will be replaced by CRLF in tests/sys/TS002.yml.
The file will have its original line endings in your working directory.
warning: LF will be replaced by CRLF in tests/sys/TS004.yml.
The file will have its original line endings in your working directory.
reordered document: TS
```

These warnings come from Git as a sub-process of the main Doorstop processes,
so the solution is to add the following to your `.gitattributes` file:

```
*.yml text eol=lf
```

From [Git's documentation](https://git-scm.com/docs/gitattributes):

> This setting forces Git to normalize line endings [for \*.yml files] to LF on checkin and prevents conversion to CRLF when the file is checked out.
