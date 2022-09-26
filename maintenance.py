
import sediment_traps

import os
from shutil import copy2
from pathlib import Path
import json

def run_maintenance():

	# needed for colored print to work
	os.system("")
	
	settings_path = "settings_temp_m.ini"
	# copy settings file to avoid corruption
	if Path("settings_temp_s.ini"):
		copy2("settings_temp_s.ini", settings_path)
	else:
		copy2("settings.ini", settings_path)
	
	# load json data
	with open("simulation_scenarios.json") as f:
		sim_data = json.load(f)
	
	variations = []
	
	# test scenarios, not run but used for settings modification
	for scenario in sim_data["maintenance"]:
		variations.append({"maintenance_id": "maintenance_" + sim_data["maintenance"][scenario]["max_capacity"] + "kg_" + sim_data["maintenance"][scenario]["maintenance_interval"] + "d", \
							"suppress_output": "1", \
							"run_simulations": "0", \
							"rank_junctions": "0", \
							"max_capacity": sim_data["maintenance"][scenario]["max_capacity"], \
							"maintenance_interval": sim_data["maintenance"][scenario]["maintenance_interval"]})
	
	##########
	
	count = 0
	for variation in variations:
		# change settings
		sediment_traps.write_settings(settings_path, variation)
		# read settings from file
		settings = sediment_traps.read_settings(settings_path)
		# do the simulations
		print("--------------------")
		sediment_traps.simulate_scenarios(settings_file=settings_path)
		print("--------------------")
		# increase counter
		count += 1
		# calculate maintenance and export to results file
		sediment_traps.export_maintenance(settings)
		# copy the results file to results folder
		if not os.path.isdir("maintenance"): os.mkdir("maintenance")
		new_path = "results_" + settings["res_id"] + "_" + variation["maintenance_id"] + ".xlsx"
		copy2(settings["results_file"], "maintenance/" + new_path)
		# delete the temporary results file
		os.unlink(settings["results_file"])
	
	# delete backup file
	os.unlink(settings_path)

if __name__ == "__main__":
	run_maintenance()


