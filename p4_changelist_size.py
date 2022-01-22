import sys
import os
import configparser
import time

import P4

MEGABIT_SIZE = 1048576

config = configparser.ConfigParser()
config.read("config.ini")

p4 = P4.P4()
p4.connect()


def main():
	if len(sys.argv) < 2:
		print("Usage: p4_changelist_size.py <changelist>")
		sys.exit(1)

	changelist = sys.argv[1]
	cl_files = get_depot_paths_by_cl(changelist)

	# Get the size of the files
	total_size = 0
	for file in cl_files:
		try:
			file["size"] = os.path.getsize(file["path"])
			total_size += file["size"]
			print(f"{convert_bytes_to_human_readable(file['size'])} - {file['clientFile']}")
		except FileNotFoundError:
			print(f"File not found: {file['clientFile']}")
	print("________________________________________")
	print(f"File Count: {len(cl_files)}")
	print(f"Total Size: {convert_bytes_to_human_readable(total_size)}")
	print(f"Estimated Upload Time: {convert_second_to_human_readable(estimate_upload_time_in_seconds(total_size))}")

def get_depot_paths_by_cl(changelist):
	all_opened = p4.run_opened()
	depot_paths = [
		file["depotFile"] for file in all_opened if file["change"] == str(changelist)
	]
	return p4.run_where(depot_paths)


def estimate_upload_time_in_seconds(total_size):
	size_in_bits = total_size * 8
	speed_in_bits = config.getfloat("UploadSpeed_Mbps") * MEGABIT_SIZE
	return = size_in_bits / speed_in_bits


def convert_second_to_human_readable(seconds):
	ty_res = time.gmtime(seconds)
	return time.strftime("%H:%M:%S", ty_res)


def convert_bytes_to_human_readable(bytes):
	if bytes == 0:
		return "0"
	units = ["B", "KB", "MB", "GB", "TB", "PB"]
	i = 0
	while bytes >= 1024:
		bytes /= 1024
		i += 1
	return "{:.2f} {}".format(bytes, units[i])


if __name__ == "__main__":
	main()