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
