# swmm-sediment-traps
 


# Installation

The code requires the pyswmmm package, available at 

https://github.com/OpenWaterAnalytics/pyswmm

This can be installed by running pip 

```
pip install pyswmm
```

If there are errors encountered, this may be due to the swmm-toolkit package not being properly installed. If this happens, download it from 

https://github.com/OpenWaterAnalytics/swmm-python

and install the .whl file

```
pip install path/to/the/file.whl
```

Make sure you are running a compatible version of Python!
As of 16.08.2022, Python 3.6, 3.8, 3.9 have been tested. 

When running the code, if there is a pyswmm error where solver.py is not being found, go to the python site-packages and copy all .dll files from swmm_toolkit/ into swmm/toolkit/.




