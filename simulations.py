
import sediment_traps
import maintenance

import os
from shutil import copy2
from pathlib import Path
import json

def main():

	# needed for colored print to work
	os.system("")

	settings_path = "settings_temp_s.ini"
	# copy settings file to avoid corruption
	copy2("settings.ini", settings_path)
	
	# load json data
	with open("simulation_scenarios.json") as f:
		sim_data = json.load(f)
	
	variations = [{param: sim_data["simulation_scenarios"][scenario][param] for param in sim_data["simulation_scenarios"][scenario]} for scenario in sim_data["simulation_scenarios"]]
	
	##########
	
	# change default settings
	default_settings = {param: sim_data["default_settings"][param] for param in sim_data["default_settings"]}
	sediment_traps.write_settings(settings_path, default_settings)
	count = 0
	for variation in variations:
		# change simulation specific settings
		sediment_traps.write_settings(settings_path, variation)
		# read settings from file
		settings = sediment_traps.read_settings(settings_path)
		# do the simulations
		print("--------------------")
		sediment_traps.simulate_scenarios(settings_file=settings_path)
		print("--------------------")
		# increase counter
		count += 1
		# export results to file
		sediment_traps.export_results(settings)
		# copy the results file to results folder
		if not os.path.isdir("results"): os.mkdir("results")
		suffix = "_" + settings["res_id"] + "_" + settings["start_date"].replace("/", "") + "_" + settings["end_date"].replace("/", "")
		copy2(settings["results_file"], "results/" + settings["results_file"].replace(".xlsx", suffix + ".xlsx"))
		# delete the temporary results file
		os.unlink(settings["results_file"])
		# run maintenance on results
		maintenance.run_maintenance()
	
	# delete backup file
	os.unlink(settings_path)
	

if __name__ == "__main__":
	main()




