# Open-Source Standard-Cell Library Characterizer (CharLib)
This initiative is due to the many talented individuals who have worked to provide a complete open-source design flows and Process Design Kits.  We are also thankful to Goolge, Efabless, and Skywater Technology for helping push this initiative forward.

Standard cell libraries are important for System on Chip design but they do not work well without good characterization of the library.  Characterization involves documenting important properties of the cell library into a central repository that other Electronic Design Automation tools utilize.  To make matters worse, many libraries require archaic and older formats that are now legacy information.  This proposal will involve creating a new python-based cell characterizer that can be used as an open-source tool. 
  
The characterizer will take in information about each cell including number of technology layers, SPICE deck information and produce output that can be used with open-source EDA tools.  The characterizer will also utilize parallelization to run all of the SPICE decks in parallel across Google servers.  The tool will be designed to run as an open-source stand-alone tool, but could be used with other parallelization toolboxes to speed up processing.
  
The initiative will include several items that will provide support and implementation for the implementation of System on Chip libraries to many engineers, scientists, and other interested users.  Documentation will be written to be utilized as an open-source element on the creation and insertion into the Caravel eFabless harness.
  
The following items are proposed for this development:
<OL>
<LI> python-based cell characterizer
<LI> Optimizing parallelization tool and scripts to run efficiently
<LI> Output creation of libraries in liberty, LEF and other popular EDA formats.
<LI> Design flow integration for use with open-source EDA flows
<LI> Different corner characterizations and documentation.
<LI> Comparison of characterization against commercial-grade characterization tools.
<LI> All scripts to characterize libraries.
<LI> Use of common benchmarks to assess standard-cell library characterization of  SkyWater Technology libraries.
</OL>
  
James E. Stine, Jr.<br>
Oklahoma State University<br>
VLSI Computer Architecture Research Laboratory<br>
james.stine@okstate.edu<br>
  
