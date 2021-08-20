<h1>Tree Reference</h1>

A Doorstop project structure follows a hierarchal [tree
structure](https://en.wikipedia.org/wiki/Tree_structure).

The root of the tree can exist anywhere in your version control working copy.
Consider the sample project structure below. (Browning, p. 191)

```
req/.doorstop.yml
    SRD001.yml
    SRD001.YML
    tests/.doorstop.yml
          HLT001.yml
          HLT002.yml
src/doc/.doorstop.yml
        SDD001.yml
        SSD002.yml
    main.c
test/doc/.doorstop.yml
         LLT001.yml
         LLT002.yml
     test_main.c
```

In Doorstop each [document](document.md) is a folder with a `.doorstop.yml`
configuration file directly inside it.

In this sample structure, there are four documents:

- SRD = Software Requirements Document
- HLT = High Level Test document
- SDD = Software Design Document
- LLT = Low Level Tests document

A few [item](item.md) files are listed in each document folder that Doorstop has
numbered sequentially.

# References

* Browning, Jace, and Robert Adams. 2014. "Doorstop: Text-Based Requirements
  Management Using Version Control." Journal of Software Engineering and
  Applications 07 (03): 187–94. <https://doi.org/10.4236/jsea.2014.73020>.
