import P4
import sys
import os


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
	if len(sys.argv) < 2:
		print("Usage: p4_changelist_size.py <changelist>")
		sys.exit(1)
	if sys.argv[1] == "default":
		print(
			"Cannot be run on default changelist. Please move the files to a new changelist first."
		)
		sys.exit(1)

	changelist = sys.argv[1]

	p4 = P4.P4()
	p4.connect()
	# p4.run_login()

	# Get the changelist
	changelist_info = p4.run_describe(changelist)
	depot_files = changelist_info[0]["depotFile"]
	cl_files = p4.run_where(depot_files)

	# Get the size of the files
	total_size = 0
	for file in cl_files:
		try:
			file["size"] = os.path.getsize(file["path"])
			total_size += file["size"]
			print(f"{convert_bytes_to_human_readable(file['size'])} - {file['clientFile']}")
		except FileNotFoundError:
			print(f"File not found: {file['clientFile']}")

	print("Total size: {}".format(convert_bytes_to_human_readable(total_size)))