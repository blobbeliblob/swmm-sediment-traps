
# this code exports existing simulation results to excel

import sediment_traps

import os
from shutil import copy2
from pathlib import Path

def main():

	# needed for colored print to work
	os.system("")

	settings_path = "settings_temp.ini"
	# copy settings file to avoid corruption
	copy2("settings.ini", settings_path)
	
	##########
	
	# read settings from file
	settings = sediment_traps.read_settings(settings_path)
	# export results to file
	sediment_traps.export_results(settings)
	# copy the results file to results folder
	if not os.path.isdir("results"): os.mkdir("results")
	suffix = "_" + settings["res_id"] + "_" + settings["start_date"].replace("/", "") + "_" + settings["end_date"].replace("/", "")
	copy2(settings["results_file"], "results/" + settings["results_file"].replace(".xlsx", suffix + ".xlsx"))
	# delete the temporary results file
	os.unlink(settings["results_file"])

	# delete backup file
	os.unlink(settings_path)


if __name__ == "__main__":
	main()

