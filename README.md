# CharLib

## Introduction
This open-source characterization tool is modified from [libretto](https://github.com/snishizawa/).

CharLib is an open cell library characterizer. The current version supports timing and power characterization of combinational and sequential cells. We are currently working on expanding the characterization profile as well as scope of parameters.

CharLib uses the OSU 0.35um SCMOS library for testing. This will be expanded to SKY130 and GF180 at a later date.

## Dependencies
Make sure you have `ngspice` installed. If `ngspice` is not in your `PATH`, you may have to specify the absolute path to the `ngspice` binary using the `set_simulator` command or `simulator` YAML key.

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

Automatic mode scans the specified directory for YAML files with CharLib configuration settings, then characterizes cells based on those settings. Expected key-value pairs and file format are described in [yaml.md](https://github.com/stineje/CharLib/blog/main/docs/yaml.md).


### Batchfile Mode
Syntax: `python3 CharLib.py -b BATCHFILE`

Batchfile executes a sequence of CharLib commands read in from a text file with one command on each line. Typically these files use the file extension ".cmd". You can include comments by starting a line with "#". See [commands.md](https://github.com/stineje/CharLib/blob/main/docs/commands.md) for detailed information on available CharLib commands and syntax.


### Shell Mode
Syntax: `python3 CharLib.py`

Shell mode is identical to batchfile mode, but provides a command-line interface for users to enter one command at a time instead of reading a batchfile. See [commands.md](https://github.com/stineje/CharLib/blob/main/docs/commands.md) for detailed information on available CharLib commands and syntax.