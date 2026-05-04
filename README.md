# CharLib: An open-source standard cell library characterizer

- 🔩 Supports combinational and sequential cells
- 📈 Plots timing and I/O voltages
- 🧑‍💻 Easy-to-use, with YAML-based configuration
- 🐍 Implemented in Python 3 with a modified PySpice backend
- 🌶️ Compatible with ngspice and Xyce

## Introduction
CharLib is an open-source standard cell library characterizer. The current version supports NLDM
timing characterization of combinational and sequential cells.

See the [documentation](https://stineje.github.io/CharLib/) for more details, including:
- [Installation instructions](https://stineje.github.io/CharLib/chapters/02_installation.html)
- [Detailed usage information](https://stineje.github.io/CharLib/chapters/03_user_guide.html)
- [Configuration syntax reference](https://stineje.github.io/CharLib/chapters/04_syntax_reference.html)
- [Information for developers & contributors](https://stineje.github.io/CharLib/chapters/05_contributing.html)

We've also published a [video tutorial](https://youtu.be/QYgwKUkUTOc?si=QH0ajlIu4vUQsxAa) that
walks through the process of getting started with CharLib, from installation to characterizing a
PDK.

## Troubleshooting
If you have any trouble using CharLib, please [open a new issue](https://github.com/stineje/CharLib/issues/new/choose).

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
