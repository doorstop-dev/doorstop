# Integrity Checks

To check a document hierarchy for consistency, run the main command:

```sh
$ doorstop
building tree...
loading documents...
validating items...

REQ
│
├── TUT
│   │
│   └── HLT
│
└── LLT
```

## Links

To confirm that every item in a document links to its parents:

```sh
$ doorstop --strict-child-check
building tree...
loading documents...
validating items...
WARNING: REQ: REQ001: no links from document: TUT
WARNING: REQ: REQ016: no links from document: LLT
WARNING: REQ: REQ017: no links from document: LLT
WARNING: REQ: REQ008: no links from document: TUT
WARNING: REQ: REQ009: no links from document: TUT
WARNING: REQ: REQ014: no links from document: TUT
WARNING: REQ: REQ015: no links from document: TUT

REQ
│
├── TUT
│   │
│   └── HLT
│
└── LLT
```
