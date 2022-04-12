<h1>Item Reference</h1>

Doorstop items are files formatted using YAML. When a new item is added using
`doorstop add`, Doorstop will create a YAML file and populate it with all
required attributes (key-value pairs). The UID of an item is defined by its
file name without the extension. An UID consists of two parts, the prefix and a
number or name. The two parts are divided by an optional separator. The prefix
and separator are determined by the document to which the item belongs. By
default, the number is automatically assigned by Doorstop. Optionally, a user
can specify a name for the UID during item creation. The name must not contain
separator characters.

Items can be stored in different formats. Two types are currently supported and
can be configured via [itemformat](document.md#itemformat) in the
`.doorstop.yml` configuration file:

The default `yaml` format stores the requirement items completely as yaml.
Advantage is the standardized and easily parsable format in case the files
need to be processed furher. The disadvantage is that there is little editor
support when writing longer requirement texts, as the text need to adhere to the
yaml formatting rules (e.g. indentation).

The alternative `markdown` format stores requirement items as markdown text with
yaml frontmatter. This concept is used by many other tools as well (e.g. 
[jekyll](https://jekyllrb.com/docs/front-matter/)). With this format, the
`header` attribute is automatically derived from the first *level 1* header 
line within the text, the remaining content of the markdown text section 
is used as `text` attribute.

Example item in `yaml` format: `REQ_000.yml`

```yaml
active: true
derived: false
header: |
  Identifiers
level: 2.1
links: []
normative: true
ref: ''
reviewed: 9TcFUzsQWUHhoh5wsqnhL7VRtSqMaIhrCXg7mfIkxKM=
text: |
  Doorstop **shall** provide unique and permanent identifiers to linkable
  sections of text.
```

The equivalent item in `markdown` format: `REQ_000.md`

```text
---
active: true
derived: false
level: 2.1
links: []
normative: true
ref: ''
reviewed: 9TcFUzsQWUHhoh5wsqnhL7VRtSqMaIhrCXg7mfIkxKM=
---

# Identifiers

Doorstop **shall** provide unique and permanent identifiers to linkable 
sections of text.
```

Regarding the documentation below both formats are equivalent, besides the
specific `header` and `text` handling as shown above. The decision can be based
on whether the better text editing support of the `markdown` format or the
consistent yaml structure is more important. The formats can also be freely 
mixed within a [document tree](tree.md), the decision can be made and configured
per document.

# Standard Item Attributes

## `active`

Determines if the item is active (true) or not (false). Only active items are
included when the corresponding document is published. Inactive items are
excluded from validation.

The value of this attribute does **not** contribute to the
[fingerprint](item.md#reviewed) of the item.

## `derived`

Indicates if the item is derived (true) or not (false).

[AcqNotes](http://www.acqnotes.com/acqnote/tasks/derived-requirements) defines derived requirements as:

> '...requirements that are not explicitly stated in the set of stakeholder requirements yet is required to satisfy one or more of them. They also arise from constraints, consideration of issues implied but not explicitly stated in the requirements baseline, factors introduced by the selected architecture, Information Assurance (IA) requirements and the design.'

Doorstop does not expect parent links on derived items.

The value of this attribute does **not** contribute to the
[fingerprint](item.md#reviewed) of the item.

## `normative`

Indicates if the item is normative (true) or non-normative (false).

[Wikipedia on Normative](https://en.wikipedia.org/wiki/Normative) in standards documents:

> 'In standards terminology still used by some organizations, "normative" means
> "considered to be a prescriptive part of the standard". It characterizes
> that part of the standard which describes what ought (see philosophy above) to
> be done within the application of that standard. It is implicit that
> application of that standard will result in a valuable outcome (ibid.). For
> example, many standards have an introduction, preface, or summary that is
> considered non-normative, as well as a main body that is considered normative.
> "Compliance" is defined as "complies with the normative sections of the
> standard"; an object that complies with the normative sections but not the
> non-normative sections of a standard is still considered to be in compliance.'

The value of this attribute does **not** contribute to the
[fingerprint](item.md#reviewed) of the item.

## `level`

Indicates the presentation order within a document. A level of 1.1 will display
above level 1.2 and 1.1.5 displays below 1.1.2.

If the level ends with .0 and the item is non-normative, Doorstop will treat the
item as a document heading. See the [text](item.md#text)-section for an
example.

The value of this attribute does **not** contribute to the
[fingerprint](item.md#reviewed) of the item.

If you edit the item file by hand or use other tools be aware of the implicit
typing rules in YAML.  For example the following level value

```yaml
level: 1.10
```

will parsed as a 1.1 float value.  Doorstop will interpret this as level 1.1
and store this level in the item file.  Use quotes around non-float values,
e.g. `level: '1.10'`.

## ``header``

Gives a header (i.e. title) for the item. It will be printed alongside the item
UID when published as HTML and Markdown. Links will also include the header
text.  This is **different** from a [heading item](item.md#example-heading).

The value of this attribute does **not** contribute to the
[fingerprint](item.md#reviewed) of the item.

### Example: Header

TST007.yml

```yaml
level: 1.5
normative: true
links:
- REQ023: null
header: |
    Gradual Temperature Drop Test
text: |
    Lower the external air temperature gradually from 0 to -15 degrees Celsius over a period of 30 minutes.
    Ensure the system performs a safe shutdown when -15 degrees Celsius is reached.
```

When this item is published, Doorstop will place the item's Header next to its UID.

```
TST007 Gradual Temperature Drop Test
  Lower the external air temperature gradually from 0 to -15 degrees Celsius over a period of 30 minutes.
  Ensure the system performs a safe shutdown when -15 degrees Celsius is reached.

  Parent Item: REQ023 Temperature Interlock
```

## `reviewed`

Each item has a fingerprint. By default, the UID of the item, the values of the
[text](item.md#text) and [ref](item.md#ref) attributes, and the UIDs of the
[links](item.md#links) attribute contribute to the fingerprint. Optionally,
values of extended attributes can be added to the fingerprint through a
[document configuration option](item.md#extended-reviewed-attributes).

The value of the *reviewed* attribute indicates the fingerprint of the item
when it was last reviewed. "null" if the item has not yet been reviewed.
Doorstop will use this to detect unreviewed changes to an item by comparing the
current item fingerprint to the last reviewed fingerprint.  The fingerprint
hash algorithm is SHA256 stored in URL-safe Base64 encoding.

You should not calculate this value manually, use `doorstop review`.

## `links`

A list of links to parent item(s). A link indicates a relationship between two
items in the document tree.

In the following example, `REQ001` is a parent to the item.

```yaml
links:
- REQ001: avwblqPimDJ2OgTrRCXxRPN8FQhUBWqPIXm7kSR95C4=
```

A link consists of two parts, the parent item UID and the
[fingerprint](item.md#reviewed) of the parent when it last reviewed. If the
link has not yet been reviewed, the fingerprint is set to "null" or omitted.

```yaml
links:
- REQ001: null
```

is equivalent to

```yaml
links:
- REQ001
```

In the cases where no fingerprint exists or a null-fingerprint is specified,
Doorstop will add a new fingerprint whenever a review occurs.

The link fingerprint is used by Doorstop to detect when a parent item is
changed, as a convenience to the writer since such change may also affect its
children.

Only the UID part of the link contributes to the fingerprint of the item (the
item of the reviewed attribute, not the parent item of the link).  The
fingerprint of the link is does **not** contribute to the fingerprint of the
item.

## `references` (new array behavior)

An array of external references. An item may reference a number of external
files. The external references are displayed in a published document.

Doorstop will search in the project root for a file matching the specified
reference. If multiple matching files exist, the first found will be used.

The value of this attribute contributes to the [fingerprint](item.md#reviewed)
of the item.

### Example: Reference files

```yaml
references:
- path: tests/test1.cpp
  type: file
- path: tests/test2.cpp
  type: file
```

### Note: new behavior vs old behavior

Note: Newer `references` attribute is a new array behavior compared to the 
original `ref` attribute's string behavior. The old behavior supports referencing
only one file via file name or referencing a file that contains a given
keyword.

The new behavior of `references` attribute allows referencing many files. The
old behavior matching a specified keyword is enabled via optional `keyword`
parameter:

```yaml
references:
- path: tests/test1.cpp
  type: file
  keyword: REQ1
- path: tests/test2.cpp
  type: file
  keyword: REQ2
```

Doorstop will search a specified file to find the specified reference.

## `ref` (deprecated behavior, see 'references')

Please check the "`references` (new array behavior)" section before reading further.

External reference. An item may reference an external file or a line in an
external file. An external reference is displayed in a published document.

Doorstop will search the project root and it's sub-directories for a filename
matching the specified reference. If multiple matching files exist, the first
found will be used.

If a file is not found, Doorstop will also search the contents of all text-files
in the project root and it's sub-directories. If a line contains the referenced
keyword, Doorstop will reference the file and line number where it found the
keyword. If the keyword is found in multiple lines or files, the first found
will be used.

A file is considered a text-file unless its file extension is listed in
`SKIP_EXTS` (settings.py).

The value of this attribute contributes to the [fingerprint](item.md#reviewed)
of the item.

### Example: Reference keyword

```yaml
ref: 'TST001'
```

References the filename and line number of a text-file that contains the
keyword "TST001".

### Example: Reference file

```yaml
ref: 'test-tst001.c'
```

References a file called "test-tst001.c".

If a reference is specified and Doorstop is unable to find it, Doorstop will
exit with an error unless reference checking is disabled.

## `text`

Item text. This is the main body of the item. Doorstop treats the value as
markdown to support rich text, images and tables. To specify a multi-line text,
use block scalar types as specified by the YAML standard.

The value of this attribute contributes to the [fingerprint](item.md#reviewed)
of the item.

### Example: Heading

REQ001.yml

```yaml
level: 1.1.0
normative: false
text: |
    This is the heading

    This is some text that goes into chapter 1.1.0.
```

When this item is published, Doorstop will create a new heading with the text
"1.1.0 This is the heading" and put the remaining text into its body.

### Example: Normative item

REQ001.yml

```yaml
level: 1.1.0
normative: true
text: |
    Doorstop **shall** support exporting to the ReqIF file format.
```

When this item is published, Doorstop will create a new heading with the text
"1.1.0 REQ001" and put the all of the text in its body.

### Example: LaTeX-like math expressions

You can use math expressions in LaTeX interpreted by the markdown extension
[python-markdown-math](https://pypi.org/project/python-markdown-math/) and rendered by
[MathJax](https://github.com/mathjax/MathJax), when using the HTML publisher.

TST008.yml

```yaml
level: 1.6
normative: true
links:
- REQ023: null
text: |
  When $a \ne 0$, there are two solutions to \(ax^2 + bx + c = 0\) and they are
  $$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$
```

# Extended Item Attributes

In addition to the standard attributes, Doorstop will allow any number of custom
extended attributes (key-value pairs) in the YAML file. The extended attributes
will not be part of a published document, but they can be queried by a 3rd party
application through the REST interface or the Python API.

In this example, an extended attribute `invented-by` is added to the item.

```yaml
invented-by: jane@example.com
```

## Defaults for extended attributes

Optionally, you can add custom default values for extended attributes.  Add
them as key-value pairs to the `defaults` dictionary under the `attributes`
section in the corresponding document configuration file `.doorstop.yml`.
There is no command to maintain this configuration option.  You have to edit
the document configuration file `.doorstop.yml` by hand.

```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    attribute-key-0: a scalar default value
    attribute-key-1:
    - default values can
    - be lists
    attribute-key-2:
      default: values can
      be: dictionaries
    attribute-key-3: ... default values can be arbitrarily complex
```

## Extended reviewed attributes

By default, the values of extended attributes do **not** contribute to the
[fingerprint](item.md#reviewed) of the item.  Optionally, you can add the
values of extended attributes to the fingerprint through the `reviewed` list
under the `attributes` section in the corresponding document configuration file
`.doorstop.yml`.  The `reviewed` list must be a non-empty list of attribute
keys.  There is no command to maintain this configuration option.  You have to
edit the document configuration file `.doorstop.yml` by hand.

```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  reviewed:
  - type
  - verification-method
```

If attributes listed in `reviewed` do not exist in an item of this document,
then these attributes are skipped in the fingerprint calculation and no warning
is issued by the validation command `doorstop`.  Validation of items against a
template should be done by third-party tools.  Changing the order of reviewed
attributes listed in the document configuration changes the fingerprint of
existing item of the documents which have these attributes.  Adding new
reviewed attributes to the document configuration does not change the
fingerprint of existing items of the document, if they do not have them,
otherwise the fingerprint changes.  Removing a reviewed attribute from the
document configuration changes the fingerprint of all items of the document
with such an attribute. The type of the values, empty strings, lists, and
dictionaries affect the fingerprint.

## Publishing extended attributes

Introduced in v2.2, Doorstop can include extended attributes in published output.

Edit the document configuration file `.doorstop.yml` by hand to include the desired attributes.

For example, to include the `invented-by` extended attribute key and value in the published output:

```yaml
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  publish:
    - invented-by
```