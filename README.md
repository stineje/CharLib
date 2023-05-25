# CharLib

## Introduction
CharLib is an open cell library characterizer. The current version supports timing characterization and power characterization of combinational and sequential cells. We are currently working on expanding the characterization profile as well as scope of parameters.

CharLib uses OSU 0.35um SCMOS library for testing. This will be expanded to SKY130 and GF180 shortly.

## Preconditions
Make sure you have `ngspice` installed. If `ngspice` is not in your `PATH`, you may have to specify the absolute path to the `ngspice` binary using the `set_simulator` command. 

## How to use
There is a simple Makefile that can run the characterization for a target library of standard cells. This defaults to OSU350. SKY130 and GF180 targets will be added in the future. 

CharLib has three distinct operating modes:

* Shell mode (default)
* Batchfile mode
* Automatic mode

Using CharLib in shell or batchfile mode is a very manual process: you enter commands to configure the characterizer and add your standard cells, then execute characterization and export the results. Automatic mode requires a bit of setup, but can be much easier for large standard cell libraries.


### Shell Mode
Syntax: `python3 CharLib.py`

Shell mode starts an interactive shell where users can enter a single command at a time. See **Command Syntax** for information on available commands.


### Batchfile Mode
Syntax: `python3 CharLib.py -b BATCHFILE`

This mode takes in a text file BATCHFILE with one command on each line. Typically these files use the file extension ".cmd". You can include comments by starting the line with "#". 

Batch files usually have three main sections: 

1. Library configuration
    - Here library-wide settings (such as output filenames) are configured. 
2. Simulation configuration
    - Here simulation data (such as VDD and VSS names and voltages) are configured.
3. Cell-specific settings
    - Here settings for each cell are provided. This varies depending on cell type, but usually includes cell name and SPICE files at minimum.

See **Command Syntax** below for more information.


### Automatic Mode (Coming soon)
Syntax: `python3 CharLib.py -l LIBRARY_PATH`

This mode parses a library of standard cells and attempts to generate a batchfile for that library. If successful, the batchfile is run immediately.

There is some setup work required prior to running in automatic mode. Library and simulation configuration details must be added to a "lib_settings.json" file in directory specified by LIBRARY_PATH. An example of what this should look like is provided in the test/spice_osu350 folder. 

If CharLib successfully generates a batchfile for the standard cell library, it will place that batchfile in the directory specified by LIBRARY_PATH. Subsequent runs in automatic mode will check for this batchfile and use it to run characterization. This allows users to make tweaks to the generated batchfile if desired. If you want to generate a new batchfile, you should delete the existing batchfile prior to running CharLib. 

### References
[1] M. Mellor, A. Mahujan, and J. E. Stine, "CharLib: an open-source characterization tool written in Python", 2023.<br>
[2] Synopsys, "What is Library Characterization?", https://www.synopsys.com/glossary/what-is-library-characterization.html, 2023 <br>
[3] Shinichi NISHIZAWA, Toru NAKURA, libretto: An Open Cell Timing Characterizer for Open Source VLSI Design, IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences, 論文ID 2022VLP0007, [早期公開] 公開日 2022/09/13, Online ISSN 1745-1337, Print ISSN 0916-8508, https://doi.org/10.1587/transfun.2022VLP0007, https://www.jstage.jst.go.jp/article/transfun/advpub/0/advpub_2022VLP0007/_article/-char/ja, <br>
[4] I. K. Rachit and M. S. Bhat, "AutoLibGen: An open source tool for standard cell library characterization at 65nm technology," 2008 International Conference on Electronic Design, Penang, Malaysia, 2008, pp. 1-6, doi: 10.1109/ICED.2008.4786726. <br>


