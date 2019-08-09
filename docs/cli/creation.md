# Parent Document

A document can be created inside a directory that is under version control:

```sh
$ doorstop create REQ ./reqs
created document: REQ (@/reqs)
```
Note: Only one root parent requirements document is allowed per version controlled directory.

Items can be added to the document and edited:

```sh
$ doorstop add REQ
added item: REQ001 (@/reqs/REQ001.yml)

$ doorstop edit REQ1
opened item: REQ001 (@/reqs/REQ001.yml)
```

# Child Documents

Additional documents can be created that link to other documents:

```sh
$ doorstop create TST ./reqs/tests --parent REQ
created document: TST (@/reqs/tests)
```

Items can be added and linked to parent items:

```sh
$ doorstop add TST
added item: TST001 (@/reqs/tests/TST001.yml)

$ doorstop link TST1 REQ1
linked item: TST001 (@/reqs/tests/TST001.yml) -> REQ001 (@/reqs/REQ001.yml)
```

It is not allowed to create links which would end up in a self reference or
cyclic dependency.

# Document Configuration

The settings and attribute options of each document are stored in a
corresponding `.doorstop.yml` file.  Some configuration options can be set via
`doorstop create` command line parameters such as the document *prefix*, the
item UID *digits*, and the *parent* prefix.  Others can only be changed by
manually editing the configuration file.  The list of options follows:

* *settings*

  * *digits*: defines the number of digits in an item UID. The default value
    is 3.  Optionally, you can set it through the `-d` command line option of
    the `doorstop create` command.  It is a mandatory and read-only document
    setting.

  * *parent*: defines the parent document prefix.  You set it through the `-p`
    command line option of the `doorstop create` command.  It is an optional
    and read-only document setting.

  * *prefix*: defines the document prefix.  You set it through the prefix of
    the `doorstop create` command.  It is a mandatory and read-only document
    setting.

  * *sep*: defines the separator between the document prefix and the number in
    an item UID.  The default value is the empty string.  You have to set it
    manually before an item is created.  Afterwards, it should be considered as
    read-only.  This document setting is mandatory.

* *attributes*

  * *defaults*: defines the
    [defaults for extended attributes](../reference/item.md#defaults-for-extended-attributes).
    This is an optional document configuration option.

  * *reviewed*: defines which
    [ extended attributes contribute to the item fingerprint](../reference/item.md#extended-reviewed-attributes).
    This is an optional document configuration option.

In the document configuration files, you can include other YAML files through a
value tagged with `!include`.  The path to the included file is always relative
to the directory of the file with the include tag.  Absolute paths are not
supported.  Please have a look at this example:

.doorstop.yml
```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    text: !include path/to/file.yml
```

path/to/file.yml
```yaml
|
  Some template text, which may
  have several
  lines.
```
