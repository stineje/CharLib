# CharLib


Standard cell libraries are important for System on Chip design but they do not work well without good characterization of the library.  Characterization involves documenting important properties of the cell library into a central repository that other Electronic Design Automation tools utilize.  To make matters worse, many libraries require archaic and older formats that are now legacy information.  This proposal will involve creating a new python-based cell characterizer that can be used as an open-source tool. <BR>
<BR>
The characterizer will take in information about each cell including number of technology layers, SPICE deck information and produce output that can be used with open-source EDA tools.  The characterizer will also utilize parallelization to run all of the SPICE decks in parallel across Google servers.  The tool will be designed to run as an open-source stand-alone tool, but could be used with other parallelization toolboxes to speed up processing.<BR>
<BR>      
The initiative will include several items that will provide support and implementation for the implementation of System on Chip libraries to many engineers, scientists, and other interested users.  Documentation will be written to be utilized as an open-source element on the creation and insertion into the Caravel eFabless harness.<BR>
<BR>
The following items are proposed for this development:
<OL>
<li>python-based cell characterizer
<li>Optimizing parallelization tool and scripts to run efficiently
<li>Output creation of libraries in liberty, LEF and other popular EDA formats.
<li>Design flow integration for use with open-source EDA flows
<li>Different corner characterizations and documentation.
<li>Comparison of characterization against commercial-grade characterization tools.
<li>All scripts to characterize libraries.
<li>Use of common benchmarks to assess standard-cell library characterization of  SkyWater Technology libraries.

Further Development

After the characterization library has been developed, additional funding could enable expansion of usage for memory characterization.
