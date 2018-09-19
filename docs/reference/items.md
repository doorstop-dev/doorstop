# Overview

Doorstop items are files formatted using YAML. When a new item is added using
```doorstop add```, Doorstop will create a YAML file and populate it with all
required attributes (key-value pairs).

Example item:
```yaml
active: true
derived: false
level: 2.1
normative: true
reviewed: 1f33605bbc5d1a39c9a6441b91389e88
links: []
ref: ''
text: |
  Doorstop **shall** provide unique and permanent identifiers to linkable
  sections of text.
```

## Standard attributes

### active

Determines if the item is active (true) or not (false). Only active items are
included when the corresponding document is published. Inactive items are
excluded from validation.

### derived

Indicates if the item is derived (true) or not (false).

[AcqNotes](http://www.acqnotes.com/acqnote/tasks/derived-requirements) defines derived requirements as:

> '...requirements that are not explicitly stated in the set of stakeholder requirements yet is required to satisfy one or more of them. They also arise from constraints, consideration of issues implied but not explicitly stated in the requirements baseline, factors introduced by the selected architecture, Information Assurance (IA) requirements and the design.'

Doorstop does not expect parent links on derived items.

### normative

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

### level

Indicates the presentation order within a document. A level of 1.1 will display
above level 1.2 and 1.1.5 displays below 1.1.2.

If the level ends with .0 and the item is non-normative, Doorstop will treat the
item as a document heading. See the [text](items.md#text)-section for an
example.

### reviewed

Indicates the fingerprint of the item when it was last reviewed. "null" if the
item has not yet been reviewed. Doorstop will use this to detect unreviewed
changes to an item by comparing the current item fingerprint to the last
reviewed fingerprint.

You should not calculate this value manually, use ```doorstop review```.


### links

A list of links to parent item(s). A link indicates a relationship between two
items in the document tree.

In the following example, ```REQ001``` is a parent to the item.

```yaml
links:
- REQ001: 1f33605bbc5d1a39c9a6441b91389e88
```

A link consists of two parts, the parent item UID and the fingerprint of the
parent when it last reviewed. If the link has not yet been reviewed, the
fingerprint is set to "null" or omitted.

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

### ref

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
```SKIP_EXTS``` (settings.py).

#### Example: Reference keyword
```yaml
ref: 'TST001'
```

References the filename and line number of a text-file that contains the
keyword "TST001".

#### Example: Reference file
```yaml
ref: 'test-tst001.c'
```

References a file called "test-tst001.c".

If a reference is specified and Doorstop is unable to find it, Doorstop will
exit with an error unless reference checking is disabled.


### text

Item text. This is the main body of the item. Doorstop treats the value as
markdown to support rich text, images and tables. To specify a multi-line text,
use block scalar types as specified by the YAML standard.

#### Example: Heading

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

#### Example: Normative item

REQ001.yml
```yaml
level: 1.1.0
normative: true
text: |
    Doorstop **shall** support exporting to the ReqIF file format.
```

When this item is published, Doorstop will create a new heading with the text
"1.1.0 REQ001" and put the all of the text in its body.

## Extended attributes

In addition to the standard attributes, Doorstop will allow any number of
custom attributes (key-value pairs) in the YAML file. The extended attributes
will not be part of a published document, but they can be queried by a 3rd party
application through the REST interface or the Python API.

#### Example:

In this example, an extended attribute ```invented-by``` is added to the item.

```yaml
invented-by: some.guy@email.com
```


## Beta Features
### header

This is **different** from _heading_. If you want a Heading item, following instructions for Heading above.

To enable, use flag `-b header` 

Gives a header (i.e. title) for the item. It will be printed alongside the item UID when published as HTML and Markdown. Links will also include the header text. 


#### Example: Header

TST007.yml
```yaml
level: 1.5
normative: true
links:
- REQ023: null
header: |
    Gradual Temperature Drop Test
text: |
    Lower the external air temperature gradually from 0 to -15 degress Celsius over a period of 30 minutes. 
    Ensure the system performs a safe shutdown when -15 degrees Celsius is reached. 
```

When this item is published, Doorstop will place the item's Header next to its UID. 

```
TST007 Gradual Temperature Drop Test
  Lower the external air temperature gradually from 0 to -15 degress Celsius over a period of 30 minutes. 
  Ensure the system performs a safe shutdown when -15 degrees Celsius is reached. 
  
  Parent Item: REQ023 Temperature Interlock
```

