# 1.0 Automated Tests {#LLT009 }

## 1.1 LLT001 {#LLT001 }

Test adding items:

> `doorstop/core/tests/test_tree.py` (line 299)

*Parent links:* [REQ003 Identifiers](REQ.html#REQ003)

## 1.2 LLT002 {#LLT002 }

Test publishing Markdown:

> `doorstop/core/tests/test_all.py` (line 590)

*Parent links:* [REQ004 Formatting](REQ.html#REQ004)

## 1.3 LLT003 {#LLT003 }

Test publishing text:

> `doorstop/core/tests/test_all.py` (line 565)

*Parent links:* [REQ007 Viewing documents](REQ.html#REQ007)

## 1.4 LLT004 {#LLT004 }

Test getting items from a document:

> `doorstop/core/tests/test_document.py` (line 283)

*Parent links:* [REQ008 Interactive viewing](REQ.html#REQ008)

## 1.5 LLT005 {#LLT005 }

Test referencing an external file by name:

> `doorstop/core/tests/test_item.py` (line 583)

*Parent links:* [REQ001 Assets](REQ.html#REQ001)

# 2.0 Inspection Tests {#LLT010 }

## 2.1 LLT007 {#LLT007 }

These checks ensure the version control system (VCS) meets the needs of
requirements management:

- Verify the VCS includes a 'tag' feature.
- Verify the VCS stores files in a permanent and secure manner.
- Verify the VCS handles change management of files.
- Verify the VCS associates changes to existing developer acccounts.
- Verify the VCS can manage changes to thousands of files.

*Parent links:* [REQ009 Baseline versions](REQ.html#REQ009), [REQ011 Storing requirements](REQ.html#REQ011), [REQ012 Change management](REQ.html#REQ012), [REQ013 Author information](REQ.html#REQ013), [REQ014 Scalability](REQ.html#REQ014), [REQ015 Installation](REQ.html#REQ015)

## 2.2 LLT008 {#LLT008 }

These checks ensure the Python package is distributed properly:

- Verify the installation can be performed on a new computer in fewer than 10
seconds.

*Parent links:* [REQ015 Installation](REQ.html#REQ015)

