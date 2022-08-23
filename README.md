# swmm-sediment-traps

### Acknowledgements

This code was developed as part of the [HuLaKaS](http://www.itamerihaaste.net/tyomme/hankkeemme/hulakas) project, with the method and results detailed further in the accompanying [master's thesis]() report. 

### Description

The code simulates the installation of sediment traps into the sewer inlets of urban catchments parametrized in US EPA's Storm Water Management Model ([SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm)). 

### Installation

The code requires the pyswmmm package, available [here](https://github.com/OpenWaterAnalytics/pyswmm). This can be installed by running pip 

```
pip install pyswmm
```

If there are errors encountered, this may be due to the swmm-toolkit package not being properly installed. If this happens, download it [here](https://github.com/OpenWaterAnalytics/swmm-python) and install the .whl file

```
pip install path/to/the/file.whl
```

Make sure you are running a compatible version of Python!
As of 16.08.2022, Python 3.6, 3.8, 3.9 have been tested. 

When running the code, if there is a pyswmm error where solver.py is not being found, go to the python site-packages and copy all .dll files from *swmm_toolkit/* into *swmm/toolkit/*.

### Use

The code can be executed by running *run_program.bat*, which serves to run the various .py files and their functions. The simulation settings can be modified in *settings.ini* (or *simulation_scenarios.json* for automated simulation runs). 


