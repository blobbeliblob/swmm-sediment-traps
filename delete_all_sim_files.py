
# delete all simulation related files, including temporary results

import sediment_traps

import os
from shutil import copy2
from pathlib import Path

def main():

	# needed for colored print to work
	os.system("")
	
	items = os.listdir()
	for item in items:
		if item.endswith(".inp"):
			file_types = [".out", ".rpt"]
			for file_type in file_types:
				if item.replace(".inp", file_type) in items:
					print(str(item.replace(".inp", file_type)))
					os.unlink(item.replace(".inp", file_type))
					print("Item deleted\n")
	
	items = os.listdir("temp")
	for item in items:
		if item.endswith(".p") and "simulation_results" in item:
			print("temp/"+item)
			os.unlink("temp/"+item)
			print("Item deleted\n")

if __name__ == "__main__":
	main()

