# Introduction

Doorstop provides flexible options for publishing your requirements documents into various formats. You can publish individual documents or the entire document hierarchy (including trace matrix) in plain text, HTML, LaTex or Markdown. Using templates, you can customize the styling of the generated documents.

The publishing process preserves the contents and structure of your requirements (optionally including attributes) in a human-readable format. This document describes the process for generating these published documents.

Note that published documents are not intended to be imported into Doorstop. If you want to export files to later re-import them, use the  [export command](interchange.md) instead.

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

## Traceability

By default, the traceability matrix shows only traces that directly follow the document tree. You could call it a “closed layer” tree. 

Use `--full-traceability` to include almost every link: 
- Links that skip a level (TST → REQ), 
- cross to a sibling branch (SW → HW),
- or even point from a higher document to a lower one,
- Links between items of the same document are NOT shown.

- **Traceability-Matrix**: each row is a chain of linked items with at most one item per document, extended in both directions until no further linked item fits.
- **Child links**: each item lists every item that is one link apart, from any document.

You could call it a "open layer” tree. 

```sh
$ doorstop publish all ./dist/ --full-traceability
```

If all links follow the document tree, the output is the same with and without the option.


# LaTeX

Individual documents or the collection of all documents can be published as a LaTeX-format file that then can be typeset by running ```pdflatex``` on the exported files. To ensure easy compilation of a complete collection with cross-references and generated plantUML diagrams, a ```compile.sh```-file is automatically created in the export folder.

## Example individual document
```
$ doorstop publish TUT path/to/name_here_is_ignored.tex
building tree...
publishing document TUT to '<...>/path/to/name_here_is_ignored.tex'...
WARNING: LaTeX export does not support custom file names. Change in .doorstop.yml instead.
You can now execute the file 'compile.sh' twice in the exported folder to produce the PDFs!
published: <...>/path/to/name_here_is_ignored.tex
$ cd path/to/
$ . ./compile.sh
This is pdfTeX, Version <Lots of text cut out!>
$ . ./compile.sh
This is pdfTeX, Version <Lots of text cut out!>
```

## Example collection of documents
```
$ doorstop publish --latex all path/to/
building tree...
loading documents...
publishing tree to '<...>/path/to'...
You can now execute the file 'compile.sh' twice in the exported folder to produce the PDFs!
published: <...>/path/to
$ cd path/to/
$ . ./compile.sh
This is pdfTeX, Version <Lots of text cut out!>
$ . ./compile.sh
This is pdfTeX, Version <Lots of text cut out!>
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
- LaTeX: `.tex`

# Templates

Each output format also has support for templates that can adjust the formatting of the output. A template is a folder named `template` placed alongside a document's `.doorstop.yml` configuration file. By default, both LaTeX and HTML publishing require a template. Doorstops uses the built-in template by default.

A command line `--template` flag is provided to allow choosing a custom template by name, i.e., `--template sidebar`. The rules are:

- Without `--template`, the built-in template is used and any `template` folders in your documents are ignored.
- With `--template`, the `template` folders are searched for one that provides the named template. Only that folder is copied to the `template` folder of the output.
  - Documents do not need their own `template` folder to use a template: it is enough that one document in the tree provides it.
  - A template folder must be self-contained (including the shared files of the built-in template, such as the stylesheets and scripts).
  - Template names must be unique within a tree.

## HTML templates

HTML template name will instruct the publisher to use the `<name>.css` file in the template folder as formatting. E.g., the default HTML template name is `sidebar`, which then will publish the HTML documents with the `sidebar.css` included in the output.

## LaTeX templates

LaTex template name will similarly instruct the publisher to use the `<name>.yml` _and_ the `<name>.cls` files in the template folder for formatting the output documents.

Due to the rather high complexity of typesetting LaTeX documents, a configuration file `<name>.yml` must be provided to allow _doorstop_ to understand how to typeset the output documents as well as a normal LaTeX class template to provide the LaTeX specific formatting.

The default LaTeX template is `doorstop`, and is included with _doorstop_. The `doorstop.yml` file is commented to provided guidance on how to write your own LaTeX template.

# Assets

In addition to the `template` folder, an `assets` folder placed next to the
`.doorstop.yml` file for a document will also be copied to the output folder during publishing. The purpose of the `assets` folder is to contain images, diagrams or other external files that can be included in your published documents.

```
document_directory/
├── .doorstop.yml
├── assets/
│   ├── images/
│   │   ├── diagram1.png
│   │   └── screenshot.jpg
│   ├── attachments/
│   │   └── specification.pdf
│   └── other/
│       └── data.csv
└── items/
    ├── REQ001.yml
    └── REQ002.yml
```

To reference the assets in your document, you should use relative paths. The publishing process will maintain these references in the outputs. For example:

```
text: |
  The system shall process input data according to the flow diagram below:

  ![Data Flow Diagram](assets/images/diagram1.png)

  The specification is available at [this link](assets/attachments/specification.pdf)
```

This example shows an inline image (`diagram1.png`) embedded in the HTML as an image and a download link (`specification.pdf`) for a referenced file.

# Attributes

Doorstop can store additional information about the requirement in "Attribute" fields. By default, the attributes are not included in the generated documents. However, you can customize which attributes appear in published outputs by updating the document's `.doorstop.yml` file.

To include specific attributes in the published document, add a `publish` list under the `attributes` section in your `.doorstop.yml` file.

Example:
```
settings:
  digits: 3
  prefix: SYSTEM-REQ
  sep: '-'
attributes:
  publish:
    - commentary
    - rationale
    - invented-by
```

In this example, three attributes will be included in the published documents:
* `commentary` (built in attribute)
* `rationale` (custom attribute)
* `invented-by` (custom attribute)

If the attribute is empty for the source item, the attribute caption will be omitted from the published document.

The example generated markdown will look something like this:

```
### 1.2.5 SYSTEM-REQ-007 {#SYSTEM-REQ-007}

Steamboat Willie **shall** whistle while he is driving his boat.

| Attribute   | Value                                                                                         |
| ----------- | --------------------------------------------------------------------------------------------- |
| commentary  | The song should be a happy tune                                                               |
| rationale   | Whistling will help demonstrate that Steamboat Willie is having a good time and is care-free. |
| invented-by | Donald                                                                                        |
```

More information about attributes can be found in the [item](../reference/item.md#extended-item-attributes) description and [document](../reference/document.md#extended-document-attributes) extended attributes sections.