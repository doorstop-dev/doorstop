### 1.2.3 REQ001 {#REQ001}

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

*Parent links: SYS001, SYS002*

## 1.4 REQ003 {#REQ003}

Unicode: -40° ±1%

> `external/text.txt` (line 3)

*Parent links: REQ001*

## 1.5 REQ006 {#REQ006}

Hello, world!

> `external/text.txt` (line 3)
> `external/text2.txt`

*Parent links: REQ001*

## 1.6 REQ004 {#REQ004}

Hello, world!

## 2.1 Plantuml _REQ002_ {#REQ002}

Hello, world!

```plantuml format="svg_inline" alt="Use Cases of Doorstop" title="Use Cases of Doorstop"
@startuml
Author --> (Create Document)
Author --> (Create Item)
Author --> (Link Item to Document)
Author --> (Link Item to other Item)
Author --> (Edit Item)
Author --> (Review Item)
Author -> (Delete Item)
Author -> (Delete Document)
(Export) <- (Author)
(Import) <- (Author)
Reviewer --> (Review Item)
System --> (Suspect Changes)
System --> (Integrity)
@enduml
```

*Child links: TST001, TST002*

## 2.1 REQ2-001 {#REQ2-001}

Hello, world!

Test Math Expressions in Latex Style:

Inline Style 1: $a \ne 0$
Inline Style 2: \(ax^2 + bx + c = 0\)
Multiline: $$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$

*Parent links: REQ001*

*Child links: TST001*

