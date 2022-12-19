# swmm-sediment-traps

A method to assess the stormwater pollution of a catchment and the potential removal achieved through the installation of sewer-inlet-installed sediment traps. The method creates a ranking of the inlets according to the pollutant load that can be removed by installing a sediment trap in them. 

### Acknowledgements

This code was developed at Aalto University as part of the [HuLaKaS](http://www.itamerihaaste.net/tyomme/hankkeemme/hulakas) project, with the method and results detailed further in the accompanying [master's thesis](https://aaltodoc.aalto.fi/handle/123456789/116386) report. 

UPDATE: v2 of the code is detailed in the [article](). 

### Description

The code simulates the installation of sediment traps into the sewer inlets of urban catchments parametrized in US EPA's Storm Water Management Model ([SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm)). 

### Installation

Downloads are found under [Releases](https://github.com/blobbeliblob/swmm-sediment-traps/releases). 

The code requires the pyswmm package, available [here](https://github.com/OpenWaterAnalytics/pyswmm), which can be installed by running pip 

```
pip install pyswmm
```

Make sure you are running a compatible version of Python!
As of 16.08.2022, Python 3.6, 3.8, 3.9, 3.10 have been tested. 

When running the code, if there is a pyswmm error where solver.py is not being found, go to the python site-packages and copy all .dll files from *swmm_toolkit/* into *swmm/toolkit/*.

### Usage

The code can be executed by running *run_program.bat*, which serves to run the various .py files and their functions. The simulation settings can be modified in *settings.ini* (or *simulation_scenarios.json* for automated simulation runs). 

### License

see the included [license](https://github.com/blobbeliblob/swmm-sediment-traps/blob/main/LICENSE).


