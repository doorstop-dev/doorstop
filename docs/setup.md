# Setup

Doorstop can require different settings for different systems.
This page contains recommendations for setting up your repository to
accomodate a variety of systems.

**Intended Audience:** Version Control System (VCS) Repository Administrator

## Windows

### Git repository

Windows deals with line-endings differently to most systems, favouring `CRLF` (`\r\n`) over the more traditional `LF` (`\n`).

**Symptom:**\
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
so the solution to this problem is a Git setting.

**Recommendation:**\
Add the following `.gitattributes`

```
*.yml core.safeclrf=false
```

From [Git's documentation](https://git-scm.com/docs/gitattributes):

> If `core.safecrlf` is set to "true" or "warn", Git verifies if the conversion is reversible for the current setting of `core.autocrlf`.
