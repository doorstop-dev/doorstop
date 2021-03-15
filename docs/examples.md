# Advanced Setup

Running `doorstop` in Docker: [tlwt/doorstop-docker](https://github.com/tlwt/doorstop-docker)

# Sample Projects

[(add your open source project here)](https://github.com/doorstop-dev/doorstop/edit/develop/docs/examples.md)

- **[ros-safety/requirements-playground](https://github.com/ros-safety/requirements-playground)**: This is a small repo for demonstrating how Doorstop can be used to manage requirements in a C++ project.


- **ISO29148**: The documents serialized in the file `codebook-example-ISO29148.qdc`, are an example of a project based on [ISO/IEC/IEEE 29148:2018 Systems and software engineering — Life cycle processes — Requirements engineering](https://www.iso.org/standard/72089.html). To import the tree use the following steps:

```bash
export PRJ=ISO29148 # $PRJ is the root Document in the codebook sets
cd baseDirectory
git init
doorstop create $PRJ $PRJ 
doorstop  import -b docs/codebook-example-ISO29148.qdc $PRJ
```

```
ISO29148
│   
├── TPM
│   
├── SyRS
│   
├── StRS
│   
├── SRS
│   
├── RTM
│   
├── OpsCon
│   
├── MOP
│   
├── HSI
│   
├── FSM
│   
├── ConOps
│   
├── BRSchildOrfan
│   
└── BRS
    │   
    └── BRSchild
        │   
        └── BRSgrandChild
```