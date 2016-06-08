# Exporting Requirements

Documents can be exported for editing or to exchange with other systems:

    $ doorstop export TST
    TST001:
      active: true
      dervied: false
      level: 1
      links:
      - REQ001
      normative: true
      ref: ''
      text: |
        Verify the foobar will foo and bar.

Or a file can be created using one of the supported extensions:

    $ doorstop export TST path/to/tst.csv
    exporting TST to path/to/tst.csv...
    exported: path/to/tst.csv

Supported formats:

- YAML: **.yml**
- Comma-Separated Values: **.csv**
- Tab-Separated Values: **.tsv**
- Microsoft Office Excel: **.xlsx**

# Importing Requirements

Items can be created/updated from the export formats:

    $ doorstop import path/to/tst.csv TST
