
import sediment_traps

import os

def main():

	# needed for colored print to work
	os.system("")

	settings_path = "settings.ini"
	# backup settings file
	sediment_traps.restore_backup(settings_path, ".bak")
	sediment_traps.create_backup(settings_path, ".bak")
	# read settings from file
	settings = sediment_traps.read_settings(settings_path)
	# export data as gis
	sediment_traps.export_to_csv(settings)

if __name__ == "__main__":
	main()

