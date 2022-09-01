
'''
IMPORT PACKAGES
'''

# import pyswmm modules
from pyswmm import Simulation, Nodes, SystemStats
# import utility functions
from utilities import progressbar_simple, progressbar, display_progress, color_print, get_yes_no, suppress_stdout, nostdout, stdout_redirected, write_iterable, print_iterable
# for data export
from pandas import DataFrame, ExcelWriter
# for making backup copy
from shutil import copy2
from pathlib import Path
# for randomness
import random
# for colored print
import os
# for getting duration of simulations
from datetime import datetime, timedelta
import time
# for cumulative sum
from numpy import cumsum, mean
# general numpy stuff
import numpy as np
# for temporary export
import pickle
# for finding simulation results
from os import listdir
from os.path import isfile, join
# for making deep copies
import copy

# pyswmm documentation at
# https://pyswmm.readthedocs.io/en/stable/reference/index.html

'''
DEFINE FUNCTIONS
'''

# identify nodes and subcatchments of interest
# the input file is parsed and information stored in dict/list objects
# returns a dict object containing these dict/list objects
def get_points_of_interest(input_file):
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		# read subcatchment data
		subcatchments = {}	# {subcatchment_1: {outlet: junction/subcatchment, area: value}, subcatchment_2: ...}
		if "[SUBCATCHMENTS]" in lines:
			sub = []
			i = 0
			while lines[i] != "[SUBCATCHMENTS]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: sub.append(lines[i])
				i += 1
			for line in sub:
				temp = [x for x in line.split(" ") if x != ""]
				subcatchments[temp[0]] = {}
				subcatchments[temp[0]]["outlet"] = temp[2]
				subcatchments[temp[0]]["area"] = temp[3]
		# read junction data
		junctions = {}	# {junction_1: {}, junction_2: ...}
		if "[JUNCTIONS]" in lines:
			junc = []
			i = 0
			while lines[i] != "[JUNCTIONS]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: junc.append(lines[i])
				i += 1
			for line in junc:
				temp = [x for x in line.split(" ") if x != ""]
				junctions[temp[0]] = {}
		# read conduit data
		conduits = {}	# {conduit_1: {from: junction_1, to: junction_2}, conduit_2: ...}
		if "[CONDUITS]" in lines:
			cond = []
			i = 0
			while lines[i] != "[CONDUITS]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: cond.append(lines[i])
				i += 1
			for line in cond:
				temp = [x for x in line.split(" ") if x != ""]
				conduits[temp[0]] = {}
				conduits[temp[0]]["from"] = temp[1]
				conduits[temp[0]]["to"] = temp[2]
		# read land use data
		landuses = []	# [land_use_1, land_use_2, ...]
		if "[LANDUSES]" in lines:
			lu = []
			i = 0
			while lines[i] != "[LANDUSES]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: lu.append(lines[i])
				i += 1
			for line in lu:
				temp = [x for x in line.split(" ") if x != ""]
				if temp[0] not in landuses:
					landuses.append(temp[0])
		# read coverage data to determine land uses
		coverages = {}	# {subcatchment_1: {land_use_1: value, land_use_2: value, ...}, subcatchment_2: ...}
		if "[COVERAGES]" in lines:
			cov = []
			i = 0
			while lines[i] != "[COVERAGES]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: cov.append(lines[i])
				i += 1
			for line in cov:
				temp = [x for x in line.split(" ") if x != ""]
				if temp[0] not in coverages.keys():
					coverages[temp[0]] = {}
				coverages[temp[0]][temp[1]] = temp[2]
		# find subcatchments leading into junctions/nodes
		sub_of_int = []	# [subcatchment_1, subcatchment_2, ...]
		for s in subcatchments:
			if subcatchments[s]["outlet"] not in subcatchments.keys():
				sub_of_int.append(s)
		# find junctions that have incoming flow from subcatchments
		junc_of_int = []	# [junction_1, junction_2, ...]
		for s in sub_of_int:
			if subcatchments[s]["outlet"] not in junc_of_int:	# avoid duplicates
				junc_of_int.append(subcatchments[s]["outlet"])
		junc_inlets = {}	# {junction_1: [subcatchment_1, subcatchment_2, ...]}
		# find which subcatchments' runoff leads to which inlet
		sub_copy = copy.deepcopy(subcatchments)
		sub_copy_copy = [s for s in sub_of_int]
		categorised_all_subcatchments = False
		while not categorised_all_subcatchments:
			categorised_all_subcatchments = True
			for s in sub_copy:
				if s not in sub_copy_copy:
					categorised_all_subcatchments = False
					if sub_copy[s]["outlet"] in sub_copy_copy:
						sub_copy[s]["outlet"] = sub_copy[sub_copy[s]["outlet"]]["outlet"]
						sub_copy_copy.append(s)
		for j in junc_of_int:
			junc_inlets[j] = [s for s in sub_copy_copy if j == sub_copy[s]["outlet"]]
		# find junctions that have both incoming flow from subcatchments and other junctions and need to be separated
		junc_to_mod = []	# [junction_1, junction_2, ...]
		for c in conduits:
			if conduits[c]["to"] in junc_of_int and conduits[c]["to"] not in junc_to_mod:
				junc_to_mod.append(conduits[c]["to"])
		# find junctions that have incoming flow from different land uses
		cov_of_int = {}	# {subcatchment_1: {land_use_1: value, land_use_2: value, ...}, subcatchment_2: ...}
		for s in coverages:
			if s in sub_of_int:
				cov_of_int[s] = coverages[s]
		junc_cov = {}	# {land_use_1: [junction_1, junction_2, ...], land_use_2: ...}
		for landuse in landuses:
			junc_cov[landuse] = []
			for subcatchment in cov_of_int:
				if landuse in cov_of_int[subcatchment].keys() and subcatchments[subcatchment]["outlet"] not in junc_cov[landuse]:
					junc_cov[landuse].append(subcatchments[subcatchment]["outlet"])
		# find area of each land use contributing to catchment area going into each junction
		junc_area = {}	# {junction_1: {total: value, land_use_1: value, land_use_2: value, ...}, junction_2: ...}
		for j in junc_of_int:
			junc_area[j] = {"total": 0}
			for l in landuses:
				junc_area[j][l] = 0
			for s in junc_inlets[j]:
				for c in coverages[s]:
					junc_area[j][c] += float(coverages[s][c]) / 100 * float(subcatchments[s]["area"])
					junc_area[j]["total"] += float(coverages[s][c]) / 100 * float(subcatchments[s]["area"])
		return {"junctions_with_manholes": junc_of_int, "junctions_to_modify": junc_to_mod, "junction_coverages": junc_cov, "junction_areas": junc_area}

# create new junctions to separate incoming flow from subcatchments and other junctions
# returns a list with the new nodes representing manholes (+ the old nodes which were only manholes and not junctions)
def separate_junctions(input_file, data, settings):
	print("\nSeparating junctions...")
	try:
		suffix = settings["junction_suffix"]
		junc_to_mod = data["junctions_to_modify"]
		with open(input_file, "r") as f:
			lines = f.readlines()
			lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
			if "[SUBCATCHMENTS]" in lines:
				i = 0
				while lines[i] != "[SUBCATCHMENTS]":
					i += 1
				i += 1
				while lines[i] != "":
					if ";" not in lines[i]:
						temp = [x for x in lines[i].split(" ") if x != ""]
						if temp[2] in junc_to_mod:
							lines[i] = lines[i].replace(temp[2], temp[2]+suffix)	# replace outlet with new junction
					i += 1
			if "[JUNCTIONS]" in lines:
				i = 0
				while lines[i] != "[JUNCTIONS]":
					i += 1
				i += 1
				while lines[i] != "":
					if ";" not in lines[i]:
						temp = [x for x in lines[i].split(" ") if x != ""]
						if temp[0] in junc_to_mod:
							height_offset = settings["height_offset"]	# define an elevation drop to avoid errors
							exp_factor = 10**6	# used for removing inaccuracy of float addition
							lines.insert(i, lines[i].replace(temp[0], temp[0]+suffix).replace(temp[1], str((float(temp[1])*exp_factor+height_offset*exp_factor)/exp_factor)))	# create new junction based on the existing one
							i += 1
					i += 1
			if "[CONDUITS]" in lines:
				i = 0
				while lines[i] != "[CONDUITS]":
					i += 1
				i += 1
				linked_junctions = []
				ref_conduits = []
				while lines[i] != "":
					if ";" not in lines[i]:
						temp = [x for x in lines[i].split(" ") if x != ""]
						if temp[2] in junc_to_mod and temp[2] not in linked_junctions:
							conduit_length = settings["conduit_length"]	# give the conduit a length to avoid errors
							lines.insert(i, lines[i].replace(temp[0], temp[0]+suffix).replace(temp[1], temp[2]+suffix).replace(temp[3], str(conduit_length)))	# create new conduit, make its source the new junction and change it's length to 0 (since it is in the same spot)
							linked_junctions.append(temp[2])	# add to list of linked junctions to avoid duplicates
							ref_conduits.append(temp[0])	# add to list of conduits used as reference
							i += 1
					i += 1
			if "[XSECTIONS]" in lines:
				i = 0
				while lines[i] != "[XSECTIONS]":
					i += 1
				i += 1
				while lines[i] != "":
					if ";" not in lines[i]:
						temp = [x for x in lines[i].split(" ") if x != ""]
						if temp[0] in ref_conduits:
							lines.insert(i, lines[i].replace(temp[0], temp[0]+suffix))	# add new conduit cross-section
							i += 1
					i += 1
			if "[COORDINATES]" in lines:
				i = 0
				while lines[i] != "[COORDINATES]":
					i += 1
				i += 1
				while lines[i] != "":
					if ";" not in lines[i]:
						temp = [x for x in lines[i].split(" ") if x != ""]
						if temp[0] in junc_to_mod:
							coord_offset = settings["coord_offset"]
							lines.insert(i, lines[i].replace(temp[0], temp[0]+suffix).replace(temp[1], str(float(temp[1])+coord_offset)).replace(temp[2], str(float(temp[2])+coord_offset)))	# add new coordinates
							i += 1
					i += 1
			junc_of_int = []
			for node in data["junctions_with_manholes"]:
				if node not in junc_to_mod:
					junc_of_int.append(node)
			for i in range(len(lines)):
				for node in junc_of_int:
					for e in lines[i].split(" "):
						if e == node:
							lines[i] = lines[i].replace(node, node+suffix)
		with open(input_file, "w") as f:
			for line in lines:
				f.write("%s\n" % line)
		new_junctions = [x.replace(x, x+suffix) for x in data["junctions_with_manholes"]]	# modified junctions to return
		color_print("Complete", "green")
		return new_junctions
	except:
		color_print("Could not separate junctions", "red")
		return []

# add treatment to nodes in the input file
# nodes = {node: {"pollutant": , "function": }}
# remove_old determines if the already existing treatment in the input file should be removed
def add_treatment(input_file, nodes, remove_old=True):
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		if "[TREATMENT]" not in lines:
			if "[WASHOFF]" in lines:
				i = 0
				while lines[i] != "[WASHOFF]":
					i += 1
				i += 1
				while lines[i] != "":
					i += 1
				i += 1
				lines.insert(i, "[TREATMENT]")	# insert the treatment category
				i += 1
				lines.insert(i, ";;Node           Pollutant        Function  ")
				i += 1
				lines.insert(i, ";;-------------- ---------------- ----------")
				i += 1
				lines.insert(i, "")	# insert an empty line to separate it from the next category
		i = 0
		while lines[i] != "[TREATMENT]":
			i += 1
		i += 1
		while lines[i] != "":
			if remove_old:
				if ";" not in lines[i]:
					del lines[i]	# remove the existing treatment
				else:
					i += 1
			else:
				i += 1
		for node in nodes:
			lines.insert(i, node+"    "+nodes[node]["pollutant"]+"    "+nodes[node]["function"])
	with open(input_file, "w") as f:
		for line in lines:
			f.write("%s\n" % line)

# change buildup/washoff for landuses
# type = "BUILDUP" or "WASHOFF"
def change_buildup_washoff(input_file, type, landuse, coeff1, coeff2):
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		i = 0
		while lines[i] != "[" + type + "]":
			i += 1
		i += 1
		while lines[i] != "":
			if ";" not in lines[i]:
				temp = [x for x in lines[i].split(" ") if x != ""]
				if temp[0] == landuse:
					lines[i] = lines[i].replace(temp[3], coeff1).replace(temp[4], coeff2)
			i += 1
	with open(input_file, "w") as f:
		for line in lines:
			f.write("%s\n" % line)

# change simulation time steps
def change_time_steps(input_file, settings):
	with open(input_file, "r") as f:
		step_params = ["REPORT_STEP", "WET_STEP", "DRY_STEP", "ROUTING_STEP"]
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		i = 0
		while lines[i] != "[OPTIONS]":
			i += 1
		i += 1
		parameters_changed = 0
		while parameters_changed < len(step_params):
			if ";" not in lines[i] and lines[i] != "":
				temp = [x for x in lines[i].split(" ") if x != ""]
				if temp[0] in step_params:
					lines[i] = lines[i].replace(temp[1], settings[temp[0]])
					parameters_changed += 1
			i += 1
	with open(input_file, "w") as f:
		for line in lines:
			f.write("%s\n" % line)

# create treatment scenarios and return them as a list
# each scenario is a list of the nodes to receive treatment
def create_treatment_scenarios(settings, junctions, landuses):
	print("\nCreating treatment scenarios...")
	treatment_scenarios = []
	treatment_scenarios.append({})	# default scenario without treatment
	try:
		if settings["rank_junctions"]:
			inlet_sets = [[x] for x in junctions]
		elif settings["land_use_prioritization"]:
			preferred_junctions = []
			for landuse in settings["preferred_land_uses"]:
				for junction in landuses[landuse]:
					if junction not in preferred_junctions:
						preferred_junctions.append(junction)
			if settings["number_of_samples"] < len(preferred_junctions):
				inlet_sets = [random.sample(preferred_junctions, settings["number_of_samples"]) for i in range(settings["number_of_scenarios"])]
			else:
				non_preferred_junctions = [x for x in junctions if x not in preferred_junctions]
				inlet_sets = [random.sample(preferred_junctions, len(preferred_junctions)) + random.sample(non_preferred_junctions, settings["number_of_samples"]-len(preferred_junctions)) for i in range(settings["number_of_scenarios"])]
			inlet_sets = [[x+settings["junction_suffix"] if settings["separate_junctions"] else x for x in s] for s in inlet_sets]
		else:
			inlet_sets = [[x+settings["junction_suffix"] if settings["separate_junctions"] else x for x in s] for s in settings["user_scenarios"]] if settings["use_specific_scenarios"] else [random.sample(junctions, settings["number_of_samples"]) for i in range(settings["number_of_scenarios"])]
		for nodes in inlet_sets:
			treatment_data = {}
			for node in nodes:
				treatment_data[node] = {}
				treatment_data[node]["pollutant"] = settings["pollutant"]
				treatment_data[node]["function"] = settings["formula"]
			treatment_scenarios.append(treatment_data)
		color_print("Complete", "green")
	except Exception as e:
		color_print("Could not create treatment scenarios", "red")
		color_print(e, "red")
	return treatment_scenarios

# rank the simulated results according to pollutant removal
def get_ranked_solutions(sim_res, criteria):
	return sorted(sim_res, key=lambda x: x[criteria], reverse=True)

# load simulation results from exported pickle files
# the results are returned in a list
# to avoid memeory issues, the detail resolution of the results is reduced (mod_num parameter)
def get_simulation_results():
	print("\nReading simulation results...")
	scenario_count = 0 if not os.path.isdir("temp") else len([f for f in listdir("temp") if isfile(join("temp", f)) and "simulation_results" in f])
	simulation_results = []
	display_progress(0)
	for i in range(scenario_count):
		mod_num = 1000
		res = pickle.load(open("temp/simulation_results_"+str(i)+".p", "rb"))
		res["step_times"] = res["step_times"][0::mod_num]
		res["volume_per_step"] = [sum(res["volume_per_step"][you:you+mod_num]) for you in range(0, len(res["volume_per_step"]), mod_num)]
		res["tss_per_step"] = [sum(res["tss_per_step"][you:you+mod_num]) for you in range(0, len(res["tss_per_step"]), mod_num)]
		res["cumulative_volume"] = res["cumulative_volume"][0::mod_num]
		res["cumulative_tss"] = res["cumulative_tss"][0::mod_num]
		res["volume_manhole_per_step"] = [sum(res["volume_manhole_per_step"][you:you+mod_num]) for you in range(0, len(res["volume_manhole_per_step"]), mod_num)] if res["volume_manhole_per_step"] else None
		res["tss_manhole_per_step"] = [sum(res["tss_manhole_per_step"][you:you+mod_num]) for you in range(0, len(res["tss_manhole_per_step"]), mod_num)] if res["tss_manhole_per_step"] else None
		res["i"] = i
		display_progress((i+1)/scenario_count)
		simulation_results.append(res)
	color_print("Complete", "green")
	return simulation_results

# calculate pollution with max capacity and maintenance interval taken into account
def calc_maintenance_efficiency(settings):
	simulation_results = get_simulation_results()
	print("\nCalculating maintenance...")
	for res in simulation_results:
		if len(res["nodes"]) != 0:
			maintenance = []	# for each time step, 1 if maintenance, 0 if not
			time_before_maintenance = settings["maintenance_interval"]*86400	# time remaining before maintenance is scheduled
			for i in range(len(res["step_times"])-1):
				time_before_maintenance -= (res["step_times"][i+1] - res["step_times"][i]).total_seconds()
				if time_before_maintenance <= 0:
					maintenance.append(1)
					time_before_maintenance = settings["maintenance_interval"]*86400
				else:
					maintenance.append(0)
			tss_to_be_added = 0	# amount of pollutant to be added to the system total because it exceded filter capacity
			stored_pollutant = 0	# amount of pollutant currently in filter
			removal_per_step = []	# removal for each time step
			for x in range(len(res["tss_per_step"])):
				diff = simulation_results[0]["tss_per_step"][x] - res["tss_per_step"][x]
				removal_per_step.append(abs(diff))
			#for i in range(len(res["tss_manhole_per_step"])-1):
			for i in range(len(res["tss_per_step"])-1):
				if maintenance[i] == 1:	# if maintenance is scheduled
					stored_pollutant = 0	# empty filter
				filter_efficiency = float(settings["formula"].split("=")[1])	# efficiency of the filter
				if stored_pollutant > settings["max_capacity"]*(10**6):	# unit convert max capacity from kg -> mg
					#tss_to_be_added += res["tss_manhole_per_step"][i]/(1-filter_efficiency)*filter_efficiency
					tss_to_be_added += removal_per_step[i]
				else:
					#stored_pollutant += res["tss_manhole_per_step"][i]/(1-filter_efficiency)*filter_efficiency
					stored_pollutant += removal_per_step[i]
			total_TSS_maintenance = res["total_TSS"] + tss_to_be_added
			print_info = False
			if print_info:
				print("node:\t\t\t\t", res["nodes"][0])
				print("node stored pollutant:\t\t", stored_pollutant/10**6)
				print("pollutant through node:\t\t", sum(res["tss_manhole_per_step"])/10**6)
				print("system pollutant removal:\t", res["removal_mass"]/10**6)
				print("system pollutant removal 2:\t", sum(removal_per_step)/10**6)
				print("system pollutant out:\t\t", res["total_TSS_system"]/10**6)
				print("total_TSS_maintenance:\t\t", total_TSS_maintenance/10**6)
				print("maintenance > system:\t\t", total_TSS_maintenance > res["total_TSS_system"])
				print("filter efficiency:\t\t", filter_efficiency)
				print("index:\t\t\t\t", res["i"])
				print("-----")
		else:
			total_TSS_maintenance = res["total_TSS"]
		res["removal_mass_maintenance"] = res["total_TSS_system"] - total_TSS_maintenance
		res["removal_percent_maintenance"] = 0 if res["total_TSS_system"] == 0 else res["removal_mass_maintenance"] / res["total_TSS_system"] * 100
		res["maintenance_removal_potential"] = res["removal_mass"] - res["removal_mass_maintenance"]
		res["maintenance_removal_potential_percentage"] = 0 if res["removal_mass"] == 0 else res["removal_mass_maintenance"] / res["removal_mass"] * 100
	color_print("Complete", "green")
	return simulation_results

# export maintenance results to excel
def export_maintenance(settings):
	print("\nExporting results...")
	simulation_results = calc_maintenance_efficiency(settings)
	with ExcelWriter(settings["results_file"]) as writer:
		for criteria in settings["order_criteria"]:
			sim_res = get_ranked_solutions(simulation_results, criteria)
			cumulative_removal = cumsum([x["removal_percent"] for x in sim_res])
			cumulative_removal_maintenance = cumsum([x["removal_percent_maintenance"] for x in sim_res])
			mean_removal = mean([x["removal_percent"] for x in sim_res])
			cumulative_mean = cumsum([mean_removal for x in sim_res])
			mean_removal_maintenance = mean([x["removal_percent_maintenance"] for x in sim_res])
			cumulative_mean_maintenance = cumsum([mean_removal_maintenance for x in sim_res])
			DataFrame({"nodes": [str(list(x["nodes"])).replace("[", "").replace("]", "").replace("'", "").replace(settings["junction_suffix"], "") for x in sim_res], \
						"Max capacity (kg)": [settings["max_capacity"] for x in sim_res], \
						"Maintenance interval (days)": [settings["maintenance_interval"] for x in sim_res], \
						"total TSS in system (kg)": [x["total_TSS"]/10**6 for x in sim_res], \
						"TSS removal max potential (kg)": [x["removal_mass"]/10**6 for x in sim_res], \
						"TSS removal max potential (%)": [x["removal_percent"] for x in sim_res], \
						"TSS removal with maintenance (kg)": [x["removal_mass_maintenance"]/10**6 for x in sim_res], \
						"TSS removal with maintenance (%)": [x["removal_percent_maintenance"] for x in sim_res], \
						"TSS removal with maintenance (% of max potential)": [x["maintenance_removal_potential_percentage"] for x in sim_res], \
						"Cumulative removal max potential (%)": cumulative_removal, \
						"Cumulative removal max potential (mean/well %)": cumulative_mean, \
						"Cumulative removal with maintenance (%)": cumulative_removal_maintenance, \
						"Cumulative removal with maintenance (mean/well %)": cumulative_mean_maintenance}).to_excel(writer, sheet_name=criteria)
	color_print("Complete", "green")
	print("Results exported to "+settings["results_file"])

# export simulation results to excel
def export_results(settings):
	print("\nExporting results...")
	simulation_results = get_simulation_results()
	with ExcelWriter(settings["results_file"]) as writer:
		for criteria in settings["order_criteria"]:
			# order solutions from best to worst
			sim_res = get_ranked_solutions(simulation_results, criteria)
			# calculate the cumulative removal (in percent)
			cumulative_removal = cumsum([x["removal_percent"] for x in sim_res])
			# calculate the lowest cumulative removal for comparison (in percent)
			cumulative_removal_reversed = cumsum([x["removal_percent"] for x in sim_res][::-1])
			# difference between best and worst cumulative removal (in percent)
			cumulative_best_worst_difference = [cumulative_removal[i]-cumulative_removal_reversed[i] for i in range(len(cumulative_removal))]
			# average cumulative removal
			mean_removal = mean([x["removal_percent"] for x in sim_res])
			cumulative_mean = cumsum([mean_removal for x in sim_res])
			# general results
			DataFrame({"start date": [x["start"] for x in sim_res], \
						"end date": [x["end"] for x in sim_res], \
						"simulation time": [x["simulation_time"] for x in sim_res], \
						"nodes": [str(list(x["nodes"])).replace("[", "").replace("]", "").replace("'", "").replace(settings["junction_suffix"], "") for x in sim_res], \
						"total volume (10^6 liters)": [x["total_volume"]/10**6 for x in sim_res], \
						"flow error (%)": [x["flow_error"] for x in sim_res], \
						"total TSS (kg)": [x["total_TSS"]/10**6 for x in sim_res], \
						"quality error (%)": [x["quality_error"] for x in sim_res], \
						"TSS removal (kg)": [x["removal_mass"]/10**6 for x in sim_res], \
						"TSS removal (%)": [x["removal_percent"] for x in sim_res], \
						"Cumulative removal (%)": cumulative_removal, \
						"Cumulative removal (reversed %)": cumulative_removal_reversed, \
						"Cumulative removal (best-worst %)": cumulative_best_worst_difference, \
						"Cumulative removal (mean/well %)": cumulative_mean, \
						"TSS removal/area (mg/m2)": [x["removal_per_area"] for x in sim_res]}).to_excel(writer, sheet_name=criteria)
		sim_res = get_ranked_solutions(simulation_results, "removal_mass")
		# area in m2
		o5_data = {"nodes": [str(list(x["nodes"])).replace("[", "").replace("]", "").replace("'", "").replace(settings["junction_suffix"], "") for x in sim_res]}
		for area in sim_res[0]["area_covered"]:
			o5_data[area] = [x["area_covered"][area] for x in sim_res]
		DataFrame(o5_data).to_excel(writer, sheet_name="area (m2)")
		# area in %
		o6_data = {"nodes": [str(list(x["nodes"])).replace("[", "").replace("]", "").replace("'", "").replace(settings["junction_suffix"], "") for x in sim_res]}
		for area in sim_res[0]["area_covered"]:
			o6_data[area] = [x["area_covered"][area] / x["area_covered"]["total"] * 100 if x["area_covered"]["total"] != 0 else 0 for x in sim_res]
		DataFrame(o6_data).to_excel(writer, sheet_name="area (%)")
		# cumulative statistics
		mod_num = 1
		o3_data = {"time": [sim_res[0]["step_times"][i] for i in range(len(sim_res[0]["step_times"])) if i % mod_num < 1]}
		o4_data = {"time": [sim_res[0]["step_times"][i] for i in range(len(sim_res[0]["step_times"])) if i % mod_num < 1]}
		if settings["accumulative_statistics"]:
			for k in range(len(sim_res)):
				o3_data[str(k)] = [sim_res[k]["cumulative_volume"][i] for i in range(len(sim_res[k]["cumulative_volume"])) if i % mod_num < 1]
				o4_data[str(k)] = [sim_res[k]["cumulative_tss"][i]/10**6 for i in range(len(sim_res[k]["cumulative_tss"])) if i % mod_num < 1]
		DataFrame(o3_data).to_excel(writer, sheet_name="cum Vol (liter)")
		DataFrame(o4_data).to_excel(writer, sheet_name="cum TSS (kg)")
	color_print("Complete", "green")
	print("Results exported to "+settings["results_file"])

# read the user settings from the settings file
# whenever a new settings parameter is added in the settings file it should be added here as well
def read_settings(settings_file):
	settings = {}
	with open(settings_file, "r") as f:
		strings = ["input_file", \
					"pollutant", \
					"start_date", \
					"end_date", \
					"results_file", \
					"outfall_node", \
					"junction_suffix", \
					"res_id", \
					"REPORT_STEP", \
					"WET_STEP", \
					"DRY_STEP", \
					"ROUTING_STEP"]
		floats = ["height_offset", \
					"conduit_length", \
					"max_capacity", \
					"coord_offset", \
					"maintenance_interval"]
		integers = ["number_of_scenarios", \
					"number_of_samples"]
		booleans = ["create_report", \
					"restore_backup", \
					"create_backup", \
					"accumulative_statistics", \
					"use_specific_scenarios", \
					"separate_junctions", \
					"create_treatment_scenarios", \
					"run_simulations", \
					"rank_junctions", \
					"land_use_prioritization", \
					"suppress_output"]
		lists = ["preferred_land_uses", \
					"order_criteria"]
		lines = f.readlines()
		lines = [lines[x].rstrip().replace(" ", "") for x in range(len(lines))]
		for i in range(len(lines)):
			if lines[i] != "":
				if lines[i][0] != "#":
					temp = lines[i].split("=")
					param = temp[0]
					for p in strings:
						if param == p:
							val = temp[1]
					for p in floats:
						if param == p:
							val = float(temp[1])
					for p in integers:
						if param == p:
							val = int(temp[1])
					for p in booleans:
						if param == p:
							val = int(temp[1])
					for p in lists:
						if param == p:
							val = [x for x in temp[1].split(",")]
					if param == "formula":
						val = temp[1].split(";")[0] + " = " + temp[1].split(";")[1]
					if param == "user_scenarios":
						val = [x.split(",") for x in temp[1].split(";")]
					settings[param] = val
	return settings	

# change a setting in the settings file
# new_values is a dict, where each key corresponds to a settings parameter in the settings file
def write_settings(settings_file, new_values):
	with open(settings_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip().replace(" ", "") for x in range(len(lines))]
		for i in range(len(lines)):
			if lines[i] != "":
				if lines[i][0] != "#":
					temp = lines[i].split("=")
					param = temp[0]
					old_value = temp[1]
					if param in new_values.keys():
						lines[i] = lines[i].replace(old_value, new_values[param])
	with open(settings_file, "w") as f:
		for line in lines:
			f.write("%s\n" % line)

# restore from backup
def restore_backup(filepath, suffix):
	try:
		copy2(Path(filepath).with_suffix(suffix), filepath)
		color_print("\nBackup restored", "green")
	except:
		color_print("\nCould not restore backup", "red")

# create new backup copy
def create_backup(filepath, suffix):
	try:
		copy2(filepath, Path(filepath).with_suffix(suffix))
		color_print("\nBackup created", "green")
	except:
		color_print("\nCould not create backup", "red")

# exports simulation results to csv that can be imported as Delimited Text Layer in QGIS
def export_to_csv(settings):
	input_file = settings["input_file"]
	delimiter = "|"
	# subcatchments
	output_file = "subcatchments.csv"
	polygons = {}
	landuses = {}
	outlets = {}
	centroids = {}
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		# geometry
		i = 0
		while lines[i] != "[Polygons]":
			i += 1
		i += 1
		while lines[i] != "":
			if ";" not in lines[i]:
				temp = [x for x in lines[i].split(" ") if x != ""]
				if temp[0] not in polygons.keys():
					polygons[temp[0]] = []
				polygons[temp[0]].append(temp[1] + " " + temp[2])
			i += 1
		# land use
		i = 0
		while lines[i] != "[COVERAGES]":
			i += 1
		i += 1
		while lines[i] != "":
			if ";" not in lines[i]:
				temp = [x for x in lines[i].split(" ") if x != ""]
				landuses[temp[0]] = temp[1]
			i += 1
		# outlet
		i = 0
		while lines[i] != "[SUBCATCHMENTS]":
			i += 1
		i += 1
		while lines[i] != "":
			if ";" not in lines[i]:
				temp = [x for x in lines[i].split(" ") if x != ""]
				outlets[temp[0]] = temp[2]
			i += 1
		# polygon centerpoint
		for p in polygons:
			c_x = sum([float(x.split(" ")[0]) for x in polygons[p]])/len(polygons[p])
			c_y = sum([float(x.split(" ")[1]) for x in polygons[p]])/len(polygons[p])
			centroids[p] = str(c_x) + " " + str(c_y)
	with open(output_file, "w") as f:
		f.write("id" + delimiter + "features" + delimiter + "landuses" + "\n")
		for p in polygons:
			f.write(p + delimiter + "POLYGON((" + ",".join(polygons[p]) + "))" + delimiter + landuses[p] + "\n")
	# junctions
	output_file = "nodes.csv"
	points = {}
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		i = 0
		while lines[i] != "[COORDINATES]":
			i += 1
		i += 1
		while lines[i] != "":
			if ";" not in lines[i]:
				temp = [x for x in lines[i].split(" ") if x != ""]
				points[temp[0]] = temp[1] + " " + temp[2]
			i += 1
	with open(output_file, "w") as f:
		f.write("id" + delimiter + "features" + "\n")
		for p in points:
			f.write(p + delimiter + "POINT((" + points[p] + "))" + "\n")
	# manholes
	output_file = "manholes.csv"
	with open(output_file, "w") as f:
		f.write("id" + delimiter + "features" + "\n")
		for p in points:
			if p in get_points_of_interest(settings["input_file"])["junctions_with_manholes"]:
				f.write(p + delimiter + "POINT((" + points[p] + "))" + "\n")
	# conduits
	output_file = "links.csv"
	with open(input_file, "r") as f:
		lines = f.readlines()
		lines = [lines[x].rstrip() for x in range(len(lines))]	# remove new line characters
		links = {}	# {conduit_1: {from: junction_1, to: junction_2}, conduit_2: ...}
		if "[CONDUITS]" in lines:
			conduits = []
			i = 0
			while lines[i] != "[CONDUITS]":
				i += 1
			i += 1
			while lines[i] != "":
				if ";" not in lines[i]: conduits.append(lines[i])
				i += 1
			for line in conduits:
				temp = [x for x in line.split(" ") if x != ""]
				links[temp[0]] = {}
				links[temp[0]]["from"] = temp[1]
				links[temp[0]]["to"] = temp[2]
	with open(output_file, "w") as f:
		f.write("id" + delimiter + "features" + "\n")
		for p in links:
			f.write(p + delimiter + "LINESTRING((" + ",".join([points[links[p]["from"]], points[links[p]["to"]]]) + "))" + "\n")
	# subcatchment outlets
	output_file = "subcatchment_outlets.csv"
	with open(output_file, "w") as f:
		f.write("id" + delimiter + "features" + "\n")
		for p in outlets:
			if outlets[p] in polygons.keys():
				f.write(p + delimiter + "LINESTRING((" + ",".join([centroids[p], centroids[outlets[p]]]) + "))" + "\n")
			else:
				f.write(p + delimiter + "LINESTRING((" + ",".join([centroids[p], points[outlets[p]]]) + "))" + "\n")

# do the simulations
def simulate_scenarios(settings_file="settings.ini"):

	# needed for colored print to work
	os.system("")
	
	# get user settings from the settings file
	print("\nReading data from settings file...")
	settings = read_settings(settings_file)
	color_print("Complete", "green")

	# file paths
	inp_file = settings["input_file"]	# inp file path
	report_file = inp_file.replace("inp", "rpt")	# generated report file path
	output_file = inp_file.replace("inp", "out")	# generated output file path

	# restore input file from backup copy
	if settings["restore_backup"]:
		restore_backup(inp_file, ".bak")

	# make a new backup copy
	if settings["create_backup"]:
		create_backup(inp_file, ".bak")
	
	# set the time steps
	change_time_steps(inp_file, settings)

	# get data from input file about the points to modify
	print("\nReading data from input file...")
	data = get_points_of_interest(inp_file)
	landuses = data["junction_coverages"]
	areas = data["junction_areas"]	# areas in ha
	sewer_inlets = data["junctions_with_manholes"]
	color_print("Complete", "green")
	
	# get treatment scenarios
	if settings["create_treatment_scenarios"]:
		treatment_scenarios = create_treatment_scenarios(settings, sewer_inlets, landuses)
	else:
		treatment_scenarios = [{}]	# only default scenario without treatment
	
	# do swmm things
	if settings["run_simulations"]:
		
		# create temp folder for results
		if not os.path.isdir("temp"): os.mkdir("temp")
		
		# delete previous simulation results, if any
		res_files = os.listdir("temp")
		for file in res_files:
			if "simulation_results" in file and file.endswith(".p"):
				os.unlink("temp/"+file)
		
		print("\nRunning simulation...")
		
		# for total simulation time
		total_sim_time_start = time.time()
		
		#try:	# error handling in case of mid-simulation crash in swmm engine
			
		# start the timer
		timer_start = time.time()

		# model setup
		with stdout_redirected():
			if settings["create_report"]:
				sim = Simulation(inp_file, reportfile=report_file, outputfile=output_file)
			else:
				sim = Simulation(inp_file)

		# set simulation start/end time
		sim.start_time = datetime(int(settings["start_date"].split("/")[2]), int(settings["start_date"].split("/")[0]), int(settings["start_date"].split("/")[1]), 0, 0, 0)
		sim.end_time = datetime(int(settings["end_date"].split("/")[2]), int(settings["end_date"].split("/")[0]), int(settings["end_date"].split("/")[1]), 23, 59, 0)

		# simulated time in seconds
		duration = (sim.end_time - sim.start_time).total_seconds()

		# properties to investigate
		step_times = []

		# system outlet
		outfall = Nodes(sim)[settings["outfall_node"]]
		
		system_routing = SystemStats(sim)	# cumulative statistics
		inlets = [node for node in Nodes(sim) if node.nodeid in sewer_inlets]	# nodes that receive water from subcatchments
		discharge = {"system": []}	# discharge at nodes
		volume = {}
		volume_cum = {}
		volume_tot = {}
		quality = {"system": []}	# water quality (concentration)
		pollutant_load = {}			# pollutant load (mass)
		pollutant_load_cum = {}
		pollutant_load_tot = {}
		pollutant_load_removal_percent = {}		# pollutant load at node divided by system pollutant load
		pollutant_load_removal_per_area = {}
		for inlet in inlets:
			discharge[inlet.nodeid] = []
			quality[inlet.nodeid] = []
		
		# execute simulation
		step_times.append(sim.start_time)	# add initial time stamp to list of time steps to facilitate calculation of time step duration later on
		progressbar_simple(0)	# start progressbar at 0
		for step in sim:
			step_times.append(sim.current_time)	# add current time stamp to the list of time steps
			discharge["system"].append(outfall.total_inflow)	# add current system discharge to list of discharges at time steps
			quality["system"].append(outfall.pollut_quality[settings["pollutant"]])	# add current pollution to list of pollution at time steps
			for inlet in inlets:
				discharge[inlet.nodeid].append(inlet.lateral_inflow)
				quality[inlet.nodeid].append(inlet.pollut_quality[settings["pollutant"]])
			if not settings["suppress_output"]: progressbar_simple(sim.percent_complete)	# update progressbar to current completion
		
		color_print("\nComplete", "green")
		
		print("\nProcessing results")
		
		total_volume2 = system_routing.routing_stats["outflow"]
		flow_error = system_routing.routing_stats["routing_error"]
		quality_error = sim.quality_error
		
		# calculate land use of solution in regards to area (area in m2)
		area_covered = {inlet: {a: areas[inlet][a] * 10**4 for a in areas[inlet]} for inlet in areas}
		area_covered["system"] = {"total": 0}
		for landuse in landuses:
			area_covered["system"][landuse] = 0
			for inlet in areas:
				area_covered["system"][landuse] += area_covered[inlet][landuse]
				area_covered["system"]["total"] += area_covered[inlet]["total"]
		
		# calculate step durations
		step_durations = [(step_times[i+1] - step_times[i]).total_seconds() for i in range(len(step_times)-1)]
		
		# system properties
		# volume in liters
		# V_tot = sum( V_i ) = sum( Q_i * dt )
		# pollutant load in mg
		# TSS_tot = sum ( TSS_i ) = sum ( C(TSS)_i * V_i )
		volume["system"] = [discharge["system"][i] * step_durations[i] for i in range(len(discharge["system"]))]
		volume_cum["system"] = cumsum(volume["system"])
		volume_tot["system"] = sum(volume["system"])
		print("total volume: ", volume_tot["system"], total_volume2)
		pollutant_load["system"] = [quality["system"][i] * volume["system"][i] for i in range(len(quality["system"]))]
		pollutant_load_cum["system"] = cumsum(pollutant_load["system"])
		pollutant_load_tot["system"] = sum(pollutant_load["system"])
		pollutant_load_removal_percent["system"] = 0
		pollutant_load_removal_per_area["system"] = 0
		
		# inlet properties
		# note! pollutant_load gives the values of the pollutant load at the node after treatment
		for inlet in inlets:
			volume[inlet.nodeid] = [discharge[inlet.nodeid][i] * step_durations[i] for i in range(len(discharge[inlet.nodeid]))]
			volume_cum[inlet.nodeid] = cumsum(volume[inlet.nodeid])
			volume_tot[inlet.nodeid] = sum(volume[inlet.nodeid])
			pollutant_load[inlet.nodeid] = [quality[inlet.nodeid][i] * volume[inlet.nodeid][i] for i in range(len(quality[inlet.nodeid]))]
			pollutant_load_cum[inlet.nodeid] = cumsum(pollutant_load[inlet.nodeid])
			pollutant_load_tot[inlet.nodeid] = sum(pollutant_load[inlet.nodeid])
			pollutant_load_removal_percent[inlet.nodeid] = 0 if pollutant_load_tot["system"] == 0 else pollutant_load_tot[inlet.nodeid] / pollutant_load_tot["system"] * 100
			pollutant_load_removal_per_area[inlet.nodeid] = 0 if area_covered[inlet.nodeid]["total"] == 0 else pollutant_load_tot[inlet.nodeid] / area_covered[inlet.nodeid]["total"]
		
		# end the timer
		timer_end = time.time()
		
		# get duration of simulation
		hours = "{:02d}".format(int((timer_end - timer_start)//3600))
		minutes = "{:02d}".format(int(((timer_end - timer_start)%3600)//60))
		seconds = "{:02d}".format(int((timer_end - timer_start)%3600%60))
		simulation_duration = hours + ":" + minutes + ":" + seconds

		del step_times[0]	# remove start time from steps to have same amount of elements as volume and pollutant arrays
		
		color_print("\nComplete", "green")
		
		print("\nExporting simulation results")
		
		# export temporary results
		ids = ["system"]
		for inlet in inlets:
			ids.append(inlet.nodeid)
		count = 0
		for id in ids:
			exported_results = {"start": sim.start_time, \
								"end": sim.end_time, \
								"simulation_time": simulation_duration, \
								"nodes": id, \
								"total_volume": volume_tot[id], \
								"flow_error": flow_error, \
								"total_TSS": pollutant_load_tot["system"], \
								"total_TSS_system": pollutant_load_tot["system"], \
								"quality_error": quality_error, \
								"removal_mass": pollutant_load_tot[id], \
								"removal_percent": pollutant_load_removal_percent[id], \
								"removal_per_area": pollutant_load_removal_per_area[id], \
								"step_times": step_times, \
								"volume_per_step": volume[id], \
								"system_quality_per_step": pollutant_load["system"], \
								"cumulative_volume": volume_cum["system"], \
								"cumulative_tss": pollutant_load_cum["system"], \
								"area_covered": area_covered[id], \
								"area_covered_total": area_covered[id]["total"]}
			exported_results["volume_manhole_per_step"] = volume[id] if id != "system" else None
			exported_results["tss_manhole_per_step"] = pollutant_load[id] if id != "system" else None
			pickle.dump(exported_results, open("temp/simulation_results_"+str(count)+".p", "wb"))
			count += 1
		
		color_print("\nComplete", "green")
		
		# create report
		if settings["create_report"]:
			sim.report()
		# remember to close the simulation
		sim.close()
	
		# set the progressbar to complete for visual pleasure
		if not settings["suppress_output"]: progressbar_simple(1)
		
		#except Exception as e:
		#	color_print("\nSimulation failed", "red")
		#	color_print("Reason:\t"+str(e), "red")
		
		
		
		# total simulation time
		total_sim_time_end = time.time()
		hours = "{:02d}".format(int((total_sim_time_end - total_sim_time_start)//3600))
		minutes = "{:02d}".format(int(((total_sim_time_end - total_sim_time_start)%3600)//60))
		seconds = "{:02d}".format(int((total_sim_time_end - total_sim_time_start)%3600%60))
		total_sim_time = hours + ":" + minutes + ":" + seconds
		print("\nTotal simulation time: " + total_sim_time)
	
	return

'''
MAIN PROGRAM
'''

if __name__ == "__main__":
	# run simulations
	simulate_scenarios()	
	# end program
	print("\nProgram terminated")



