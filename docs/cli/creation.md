# Parent Document

A document can be created inside a directory that is under version control:

```sh
$ doorstop create REQ ./reqs
created document: REQ (@/reqs)
```

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
