# CharLib: An open-source standard cell library characterizer

- 🔩 Supports combinational and sequential cells
- 📈 Plots timing and I/O voltages
- 🧑‍💻 Easy-to-use, with YAML-based configuration
- 🐍 Implemented in Python 3 with a modified PySpice backend
- 🌶️ Compatible with ngspice and Xyce

## Introduction
CharLib is an open-source standard cell library characterizer. The current version supports timing characterization of combinational and sequential cells.

## Installation
CharLib can be installed from [PyPI](https://pypi.org/project/charlib) using pip:

```
# Install our customized version of PySpice
pip install git+https://github.com/infinitymdm/PySpice

# Install CharLib
pip install charlib
```
Make sure you also have a compatible circuit simulator. [ngspice](https://ngspice.sourceforge.io/) and [xyce](https://xyce.sandia.gov/) are currently supported.

## Usage
`charlib run path/to/library/config/`

CharLib searches the specified directory for a YAML file containing a valid cell library configuration, then characterizes the specified cells. See [yaml.md](https://github.com/stineje/CharLib/blob/main/docs/yaml.md) for information on constructing a config file.

The general process for using CharLib is as follows:
1. Acquire SPICE files and transistor models for the cells you want to characterize
2. Write a configuration YAML file for the library
3. Run CharLib

Running `charlib --help` will display lots of useful information.

## Contributing
We're glad you're interested in contributing to CharLib! See [CONTRIBUTING.md](https://github.com/stineje/CharLib/blob/main/CONTRIBUTING.md) for details on how to get involved.

## Troubleshooting
If you're having problems using CharLib, please [open a new issue](https://github.com/stineje/CharLib/issues/new/choose)

## Citing
If you use this work in your research, please cite as follows:

```bibtex
@inproceedings{mellor_charlib_2024,
    title = {{CharLib}: {An} {Open} {Source} {Standard} {Cell} {Library} {Characterizer}},
    shorttitle = {{CharLib}},
    url = {https://ieeexplore.ieee.org/document/10658687},
    doi = {10.1109/MWSCAS60917.2024.10658687},
    booktitle = {2024 {IEEE} 67th {International} {Midwest} {Symposium} on {Circuits} and {Systems} ({MWSCAS})},
    author = {Mellor, Marcus and Stine, James E.},
    month = aug,
    year = {2024},
    note = {ISSN: 1558-3899},
    keywords = {Accuracy, Circuits and systems, Design tools, Libraries, Micrometers, Process control, Silicon},
    pages = {277--281},
}
```
