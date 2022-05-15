# CharLib

<PRE>
Standard cell libraries are important for System on Chip design but they do not work well without good characterization of the library.  Characterization involves documenting important properties of the cell library into a central repository that other Electronic Design Automation tools utilize.  To make matters worse, many libraries require archaic and older formats that are now legacy information.  This proposal will involve creating a new python-based cell characterizer that can be used as an open-source tool. 
  
The characterizer will take in information about each cell including number of technology layers, SPICE deck information and produce output that can be used with open-source EDA tools.  The characterizer will also utilize parallelization to run all of the SPICE decks in parallel across Google servers.  The tool will be designed to run as an open-source stand-alone tool, but could be used with other parallelization toolboxes to speed up processing.
  
The initiative will include several items that will provide support and implementation for the implementation of System on Chip libraries to many engineers, scientists, and other interested users.  Documentation will be written to be utilized as an open-source element on the creation and insertion into the Caravel eFabless harness.
  
The following items are proposed for this development:

1.) python-based cell characterizer
2.) Optimizing parallelization tool and scripts to run efficiently
3.) Output creation of libraries in liberty, LEF and other popular EDA formats.
4.) Design flow integration for use with open-source EDA flows
5.) Different corner characterizations and documentation.
6.) Comparison of characterization against commercial-grade characterization tools.
7.) All scripts to characterize libraries.
8.) Use of common benchmarks to assess standard-cell library characterization of  SkyWater Technology libraries.
</PRE>
