
:: This file is meant to execute the user specified files

@echo off

::main menu
:menu

echo.
echo Specify the operation to run:
echo 0 = Help
echo 1 = Simulation ^(automated^)
echo 2 = Simulation ^(basic^)
echo 3 = Export results
echo 4 = Maintenance
echo 5 = Export GIS
echo 6 = Restore all backups
echo 7 = Delete all simulation files
echo exit = Terminate program
echo cls = Clear terminal

set /p input=""
IF NOT DEFINED input set input=nothing

echo.
IF %input%==1 (
	python simulations.py
)
IF %input%==2 (
	python sediment_traps.py
)
IF %input%==3 (
	python export_results.py
)
IF %input%==4 (
	python maintenance.py
)
IF %input%==5 (
	python export_gis.py
)
IF %input%==6 (
	python restore_all_backups.py
)
IF %input%==7 (
	python delete_all_sim_files.py
)

IF %input%==0 (
	echo 1. Simulation ^(automated^): Run the simulations.py file, executing various sets of simulation scenarios automatically and dynamically modifying the settings.ini file between scenarios
	echo 2. Simulation ^(basic^): Only run the simulation scenario defined in the settings.ini file
	echo 3. Export results: Export simulation results to excel ^(make sure that results exist^)
	echo 4. Maintenance: Run maintenance calculations and export results to excel
	echo 5. Export GIS: Export the SWMM parametrization into csv files that can be imported as Delimited Text Layers in QGIS
	echo 6. Restore all backups: Restore all files into their original, and delete the backup files
	echo 7. Delete all simulation files: Delete all files created for simulation scenarios, including temporary result files
)

IF %input%==exit (
	goto exit
)

IF %input%==cls (
	cls
)

IF %input%==nothing (
	cls
)

IF %input%==cmd (
	echo Command:
	set /p command=""
	%command%
)

set input=nothing

goto menu

:exit


@pause
