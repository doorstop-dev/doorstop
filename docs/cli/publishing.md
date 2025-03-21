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

Each output format also has support for templates that can adjust the formatting of the output. Any folder named `template` that is placed alongside the `.doorstop.yml` configuration file will be copied during the publishing process into the output folder. _Note: If multiple documents contain the `template` _folder, they will **all** be copied, although no overwriting is performed._

A command line `--template` flag is provided to allow choosing the template by name. By default, both LaTeX and HTML publishing formats _require_ a template! Therefore, _doorstop_ provides standard templates for these formats that will be used automatically if no template name is given during publishing.

The flag is used by providing the name of the template, i.e., `--template sidebar`.

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

| Attribute | Value |
| --------- | ----- |
| commentary | The song should be a happy tune |
| rationale | Whistling will help demonstrate that Steamboat Willie is having a good time and is care-free. |
| invented-by | Donald |
```

More information about attributes can be found in the [item](item.md#extended-item-attributes) description and [document](document.md#extended-document-attributes) extended attributes sections.
