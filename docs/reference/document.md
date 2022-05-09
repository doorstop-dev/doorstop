<h1>Document Reference</h1>

Doorstop documents are folders, with metadata stored in a configuration YAML
file `.doorstop.yml` directly below the folder.

# Standard Document Attributes

Upon [creation](../cli/creation.md), `.doorstop.yml` contains default settings.

```sh
$ doorstop create REQ ./reqs
created document: REQ (@/reqs)
```

Then open `REQ/.doorstop.yml` in any text editor:

```yaml
settings:
  digits: 3
  prefix: REQ
  itemformat: yaml
  sep: ''
```

## `settings`

Parameters that affect the entire document fall under here.

### `digits`

Defines the number of digits in an item UID. The default value is 3. Optionally,
you can set it through the `-d` command line option of the `doorstop create`
command.  It is a mandatory and read-only document setting.

### `parent`

Defines the parent document prefix.  You set it through the `-p` command line
option of the `doorstop create` command.  It is an optional and read-only
document setting.

### `prefix`

Defines the document prefix.  You set it through the prefix of the
`doorstop create` command.  It is a mandatory and read-only document setting.

### `sep`

Defines the separator between the document prefix and the number in an item UID.
The default value is the empty string.  You have to set it manually before an
item is created.  Afterwards, it should be considered as read-only.  This
document setting is mandatory.

### `itemformat`

Requirement items can be stored in different file formats. The two types
currently supported are `yaml` and `markdown`. See the [item](item.md)
documentation for more details. The default format is `yaml`.

# Extended Document Attributes

In addition to the standard attributes, Doorstop will allow any number of custom
extended attributes (key-value pairs) in the YAML file. The extended attributes
will not be part of a published document, but they can be queried by a 3rd party
application through the REST interface or the Python API.

## `attributes`

Extended document attributes fall under here.

### `defaults`

Defines the [defaults for extended
attributes](item.md#defaults-for-extended-attributes). This is an optional
document configuration option.

### `reviewed`

Defines which [extended attributes contribute to the item
fingerprint](item.md#extended-reviewed-attributes). This is an optional document
configuration option.

In the document configuration files, you can include other YAML files through a
value tagged with `!include`.  The path to the included file is always relative
to the directory of the file with the include tag.  Absolute paths are not
supported.  Please have a look at this example:

In `.doorstop.yml`:

```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    text: !include path/to/file.yml
```

In `path/to/file.yml`:

```yaml
|
  Some template text, which may
  have several
  lines.
```