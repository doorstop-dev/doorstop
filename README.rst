Introduction
============

TBD



Getting Started
===============

Requirements
------------

* Python 2.6 or 2.7
* Veracity 2.x (to update)
* Make (to build on Ubuntu)
* dos2unix (to build on Ubuntu)
* ia32-libs (to build on 64-bit Ubuntu)


Installation
------------

WorkspaceTools can be installed with ``jcipip``::

    jcipip install WorkspaceTools
    
After installation, WorkspaceTools is available on the command-line::

   ws --help
    
And the package is available under the name ``workspace_tools``::

    python
    >>> import workspace_tools
    >>> workspace_tools.__version__
    


Sample Commands
===============

Update Use Cases
----------------

Update an existing component's dependencies::

    cd src/cpp/procio
    ws update
    
Update a componet and dependnecies to the latest version::

    cd src
    ws update cpp_procio


Build Use Cases
---------------

Build a component and its dependencies::

   cd src/cpp/procio
   ws build
   