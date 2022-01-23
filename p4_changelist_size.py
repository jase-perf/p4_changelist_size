import sys
import os
import configparser
import time
from pathlib import Path
from typing import List, Tuple

from appdirs import user_config_dir
import speedtest
import P4

MEGABIT_SIZE = 1048576
CONFIG_PATH = Path(user_config_dir("p4_changelist_size")) / "config.ini"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

p4 = P4.P4()
p4.connect()


def main():
    print(f"Config file location: {CONFIG_PATH}\n")
    speed_mbps = get_upload_speed()

    changelist = sys.argv[1]
    cl_files = get_depot_paths_by_cl(changelist)

    total_size, errors = calculate_changelist_size(cl_files)

    print("________________________________________")
    if errors:
        print("\n".join(errors))
    print(f"File Count: {len(cl_files)}")
    print(f"Total Size: {convert_bytes_to_human_readable(total_size)}")
    print(
        f"Estimated Upload Time: {convert_second_to_human_readable(estimate_upload_time_in_seconds(total_size, speed_mbps))}"
    )


def get_upload_speed() -> float:
    """Return the upload speed_mbps."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        speed_mbps = config["CONNECTION"].getfloat("UploadSpeed_Mbps")
    except KeyError:
        config["CONNECTION"] = {}
        speed_mbps = None
    except ValueError:
        speed_mbps = None
    if not speed_mbps:
        print(
            (
                "______ First Time Setup ______\n"
                "Upload speed needs to be set for time estimates.\n\n"
                "If you are connecting to your Helix Core server via standard internet:\n"
                "Press REPLY button to automatically test your internet connection speed.\n\n"
                "If you are connecting to your Helix Core server via local LAN network:\n"
                "Enter your LAN speed in Mbps below and then click REPLY\n"
                "(If you aren't sure of your LAN speed, 1000 is a safe bet)."
            )
        )
        while True:
            has_manual_speed = input()
            if not has_manual_speed:
                speed_mbps = test_internet_speed()
                break
            try:
                speed_mbps = float(has_manual_speed)
                break
            except ValueError:
                print(
                    "ERROR: Please enter the NUMBER of megabits per second (As an integer or float)\n"
                    "Or leave blank to auto-test your internet speed."
                )
        config["CONNECTION"]["UploadSpeed_Mbps"] = f"{speed_mbps:.2f}"
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)
    return speed_mbps


def test_internet_speed() -> float:
    print("Testing internet speed. This will take a few seconds...", flush=True)
    s = speedtest.Speedtest()
    s.upload()
    speed_mbps = s.results.upload / MEGABIT_SIZE
    print(f"Your internet upload speed is: {speed_mbps:.2f} Mbps\n")
    return speed_mbps


def calculate_changelist_size(cl_files: List[dict]) -> Tuple[int, List[str]]:
    """
    Print the size of each file in the changelist and return the total
    size in bytes, as well a list of any errors.
    """
    total_size = 0
    errors = []
    for file in cl_files:
        try:
            file["size"] = os.path.getsize(file["path"])
            total_size += file["size"]
            print(
                f"{convert_bytes_to_human_readable(file['size']).ljust(8)} - {file['clientFile']}"
            )
        except FileNotFoundError:
            errors.append(
                f"WARNING: Changelist contains file that does not exist: {file['clientFile']}"
                "\n    Remove this file from the changelist or restore the file before submitting."
            )
    return total_size, errors


def get_depot_paths_by_cl(changelist: str) -> List[dict]:
    """Takes a changelist number (or "CONNECTION") and returns a list of dicts of all files in that changelist."""
    all_opened = p4.run_opened()
    depot_paths = [
        file["depotFile"] for file in all_opened if file["change"] == str(changelist)
    ]
    return p4.run_where(depot_paths)


def estimate_upload_time_in_seconds(
    total_size_in_bytes: int, upload_speed_mbps: float
) -> float:
    """Takes the total size of the changelist in bytes and returns the estimated upload time in seconds. Estimate based on upload speed in config.ini."""
    size_in_bits = total_size_in_bytes * 8
    speed_in_bits = upload_speed_mbps * MEGABIT_SIZE
    return size_in_bits / speed_in_bits


def convert_second_to_human_readable(seconds: int) -> str:
    ty_res = time.gmtime(seconds)
    return time.strftime("%H:%M:%S", ty_res)


def convert_bytes_to_human_readable(bytes: int) -> str:
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

    main()
