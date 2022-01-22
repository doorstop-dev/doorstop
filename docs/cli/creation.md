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

# Add Items with Custom Default Attributes

Items can be added to documents with custom default values for attributes
specified by the command line:

```sh
$ doorstop add -d defaults.yml REQ
building tree...
added item: REQ001 (@/reqs/REQ001.yml)

$ doorstop publish REQ
building tree...
1.0     REQ001

        My default text.
```

defaults.yml

```yaml
text: 'My default text.'
```

The command line specified default values override values from the document
configuration.

# Add Items with a Name in the UID

By default, new items get a number assigned by Doorstop for their UID together
with the document prefix and separator.  Doorstop allows you to specifiy an
explicit number or a name for the item UID.  Names can be only used if the
document was created with a separator.  Names cannot contain separators.
Allowed separators are '-', '\_', and '.'.

As an example, we create a document with a '-' separator:
```sh
$ doorstop create -s - REQ ./reqs
building tree...
created document: REQ (@/reqs)
```

You can add items as normal:
```sh
$ doorstop add REQ
building tree...
added item: REQ-001 (@/reqs/REQ-001.yml)
```

The first item has an UID of `REQ-001`.  Please note that this UID has the
separator of the document included.  You can specify the number part of the UID
for a new item:
```sh
$ doorstop add -n 3 REQ
building tree...
added item: REQ-003 (@/reqs/REQ-003.yml)
```

You can specify the name part of the UID for a new item:
```sh
$ doorstop add -n FOOBAR REQ
building tree...
added item: REQ-FOOBAR (@/reqs/REQ-FOOBAR.yml)
```

You can continue to add items as normal:
```sh
$ doorstop add REQ
building tree...
added item: REQ-004 (@/reqs/REQ-004.yml)
```

Your document contains now the following items:
```sh
$ doorstop publish REQ
building tree...
1.0     REQ-001

1.1     REQ-003

1.2     REQ-FOOBAR

1.3     REQ-004
```

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
