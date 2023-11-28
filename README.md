# CharLib: An open-source standard cell library characterizer

- 🔩 Supports combinational and sequential cells
- 📈 Plots timing and I/O voltages
- 🧑‍💻 Easy-to-use, with YAML-based configuration
- 🐍 Implemented in Python 3 with a modified PySpice backend
- 🌶️ Compatible with ngspice and Xyce

## Introduction
CharLib is an open cell library characterizer originally based on [libretto](https://github.com/snishizawa/libretto). The current version supports timing characterization of combinational and sequential cells.

## Installation
CharLib can be installed from [PyPI](https://test.pypi.org/project/charlib) using pip:

```
# Install our customized version of PySpice
pip install git+https://github.com/infinitymdm/PySpice

# Install CharLib
pip install charlib
```
Make sure you also have a compatible circuit simulator. [ngspice](https://ngspice.sourceforge.io/) and [xyce](https://xyce.sandia.gov/) are currently supported.

## Usage
`charlib path/to/library/config/`

CharLib searches the specified directory for a YAML file containing a valid cell library configuration, then characterizes the specified cells. See [yaml.md](https://github.com/stineje/CharLib/blob/main/docs/yaml.md) for information on constructing a config file.

The general process for using CharLib is as follows:
1. Acquire SPICE files and transistor models for the cells you want to characterize
2. Write a configuration YAML file for the library
3. Run CharLib

## References
[1] M. Mellor and J. E. Stine, "CharLib: an open-source characterization tool written in Python", 2023. <br>
[2] Synopsys, "What is Library Characterization?", https://www.synopsys.com/glossary/what-is-library-characterization.html, 2023 <br>
[3] S. Nishizawa and T. Nakura, "libretto: An Open Cell Timing Characterizer for Open Source VLSI Design," IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences, 論文ID 2022VLP0007, [早期公開] 公開日 2022/09/13, Online ISSN 1745-1337, Print ISSN 0916-8508, https://doi.org/10.1587/transfun.2022VLP0007, https://www.jstage.jst.go.jp/article/transfun/advpub/0/advpub_2022VLP0007/_article/-char/ja, <br>
[4] I. K. Rachit and M. S. Bhat, "AutoLibGen: An open source tool for standard cell library characterization at 65nm technology," 2008 International Conference on Electronic Design, Penang, Malaysia, 2008, pp. 1-6, doi: 10.1109/ICED.2008.4786726. <br>
[5] E. Salman, A. Dasdan, F. Taraporevala, K. Kucukcakar and E. G. Friedman, "Exploiting Setup-Hold-Time Interdependence in Static Timing Analysis," IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol. 26, no. 6, pp. 1114-1125, June 2007, doi: 10.1109/TCAD.2006.885834.
