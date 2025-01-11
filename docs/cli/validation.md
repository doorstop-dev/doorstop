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

By default, the validation run displays messages with a `WARNING` and `ERROR` level.
In case verbose output is enabled, also messages with an `INFO` level
are shown.

`INFO` level messages are generated under the following conditions:

* Skipped levels within the items of a document.
* No initial review done for an item.
* The prefix of an UID is not equal to the document prefix.
* The prefix of a link UID is not equal to the parent document prefix.

`WARNING` level messages are generated under the following conditions:

* A document contains no items.
* Duplicated levels within the items of a document.
* An item has an empty text attribute.
* An item has unreviewed changes.
* An item's child link is an inactive item.
* An item is linked to a non-normative item.
* An item is linked to itself.
* An item has a suspect linked to an item those fingerprint is not equal to the
  one recorded in the link.
* An item in a document with child documents has no links from an item in one of its child documents.
* A normative, non-derived item in a child document has no links.
* A non-normative items has links.
* There is a cycle of item links.

`ERROR` level messages are generated under the following conditions:

* An item's parent link is an inactive item.
* An item's link is an invalid or unknown UID.
* An external reference cannot be found.

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

## Clear Suspect Links

Each link consists of the parent item UID and the
[fingerprint](../reference/item.md#reviewed) of the parent item.  When the
fingerprint of a parent item changes, the link is reported as suspect during
validation.

```sh
doorstop
building tree...
loading documents...
validating items...
WARNING: LLT: LLT005: suspect link: REQ001

REQ
│
├── TUT
│   │
│   └── HLT
│
└── LLT
```

You can clear suspect links with the `doorstop clear` command.

```sh
$ doorstop clear LLT005
building tree...
clearing item LLT005's suspect links...
```

Optionally, you can clear only suspect links to specific parent items.

```sh
$ doorstop clear LLT005 REQ002 REQ003
building tree...
clearing item LLT005's suspect links to REQ002, REQ003...
```
