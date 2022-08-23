
# find all backup files and restore them, then delete the backup files

import sediment_traps

import os
from shutil import copy2
from pathlib import Path

def main():

	# needed for colored print to work
	os.system("")
	
	items = os.listdir()
	for item in items:
		if item.endswith(".bak"):
			file_types = [".ini", ".inp"]
			for file_type in file_types:
				if item.replace(".bak", file_type) in items:
					print(str(item.replace(".bak", file_type)))
					sediment_traps.restore_backup(item.replace(".bak", file_type), ".bak")
			# delete the backup file
			os.unlink(item)

if __name__ == "__main__":
	main()
