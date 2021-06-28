# Advanced Setup

Running `doorstop` in Docker: [tlwt/doorstop-docker](https://github.com/tlwt/doorstop-docker)

# Sample Projects

[(add your open source project here)](https://github.com/doorstop-dev/doorstop/edit/develop/docs/examples.md)

- **[ros-safety/requirements-playground](https://github.com/ros-safety/requirements-playground)**: This is a small repo for demonstrating how Doorstop can be used to manage requirements in a C++ project.


- **ISO29148**: mockup of a project based on [ISO/IEC/IEEE 29148:2018 Systems and software engineering — Life cycle processes — Requirements engineering](https://www.iso.org/standard/72089.html). The tree is serialized in the file `ISO29148_example.qdc`. Import it using the following steps:

```bash
cd some_directory
git init
doorstop create ISO29148 ISO29148
doorstop  import -b docs/ISO29148_example.qdc ISO29148
```

```
ISO29148
│   
├── PDis
│   │   
│   ├── TPM
│   │   
│   ├── RTM
│   │   
│   ├── MOP
│   │   
│   ├── FSM
│   │   
│   └── ABL
│   
├── FBL
│   │   
│   ├── SyRS
│   │   
│   └── SRS
│   
└── BRS
    │   
    ├── StRS
    │   
    ├── OpsCon
    │   
    ├── HSI
    │   
    └── ConOps
```