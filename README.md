# CharLib

## Introduction
CharLib is an open cell library characterizer originally based on [3]. The current version supports timing and power characterization of combinational and sequential cells. We are currently working on expanding the characterization profile as well as scope of parameters.

CharLib uses the OSU 0.35um SCMOS library for testing. This will be expanded to SKY130 and GF180 at a later date.

## Dependencies
CharLib uses a lightly customized version of PySpice. PySpice is compatible with ngspice and Xyce simulators; you should make sure you have one of those installed to use CharLib. CharLib defaults to the ngspice simulator, but this can be changed using the `simulator` YAML key or the `set_simulator` command.

Install information can be found at the links below:
* [ngspice](https://ngspice.sourceforge.io/download.html)
* [Xyce](https://xyce.sandia.gov/)

CharLib supports all PySpice simulator options. Available options can be found [here on the PySpice FAQ](https://pyspice.fabrice-salvaire.fr/releases/latest/faq.html#how-to-set-the-simulator).

## Usage
CharLib has three operating modes:

| Mode                         | Description |
| ---------------------------- | ----------- |
| Automatic mode (recommended) | Reads a YAML configuration file from the specified directory, then automatically characterizes cells using the provided settings. |
| Batchfile mode               | Reads and executes CharLib commands from the specified batch file. |
| Shell mode (default)         | Provides a command-line interface to execute CharLib commands one at a time. |

Using CharLib in shell or batchfile mode is a very manual process: you enter commands to configure the characterizer and add your standard cells, then execute characterization and export the results.


### Automatic Mode
Syntax: `python3 CharLib.py -l LIBRARY_PATH`

Automatic mode scans the specified directory for YAML files with CharLib configuration settings, then characterizes cells based on those settings. Expected key-value pairs and file format are described in [yaml.md](https://github.com/stineje/CharLib/blob/main/docs/yaml.md).


### Batchfile Mode
Syntax: `python3 CharLib.py -b BATCHFILE`

Batchfile executes a sequence of CharLib commands read in from a text file with one command on each line. Typically these files use the file extension ".cmd". You can include comments by starting a line with "#". See [commands.md](https://github.com/stineje/CharLib/blob/main/docs/commands.md) for detailed information on available CharLib commands and syntax.


### Shell Mode
Syntax: `python3 CharLib.py`

Shell mode is identical to batchfile mode, but provides a command-line interface for users to enter one command at a time instead of reading a batchfile. See [commands.md](https://github.com/stineje/CharLib/blob/main/docs/commands.md) for detailed information on available CharLib commands and syntax.

## References
[1] M. Mellor and J. E. Stine, "CharLib: an open-source characterization tool written in Python", 2023. <br>
[2] Synopsys, "What is Library Characterization?", https://www.synopsys.com/glossary/what-is-library-characterization.html, 2023 <br>
[3] S. Nishizawa and T. Nakura, libretto: An Open Cell Timing Characterizer for Open Source VLSI Design, IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences, 論文ID 2022VLP0007, [早期公開] 公開日 2022/09/13, Online ISSN 1745-1337, Print ISSN 0916-8508, https://doi.org/10.1587/transfun.2022VLP0007, https://www.jstage.jst.go.jp/article/transfun/advpub/0/advpub_2022VLP0007/_article/-char/ja, <br>
[4] I. K. Rachit and M. S. Bhat, "AutoLibGen: An open source tool for standard cell library characterization at 65nm technology," 2008 International Conference on Electronic Design, Penang, Malaysia, 2008, pp. 1-6, doi: 10.1109/ICED.2008.4786726. <br>
