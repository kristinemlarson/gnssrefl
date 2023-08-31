import os
import shutil
import sys

from datetime import datetime
from pathlib import Path

def remove_items():
    retain = [
    "exe", "learn-the-code", "orbits", "use-cases", ".gitkeep"]
    for item in os.listdir(Path.cwd()):
        if item not in retain and "ipynb" not in item:
            try:
                print(f"removing {item}")
                os.remove(item)
            except PermissionError:
                delete = input(f"delete directory and all of its contents?: {Path(item).resolve()} (y/n)")
                if delete == 'y':
                    print(f"removing {item}")
                    shutil.rmtree(item)


notebook_path = Path.cwd().resolve().parent / "notebooks/"


paths_to_clear = [notebook_path,
                  notebook_path / "orbits",
                  notebook_path / "exe",
                  notebook_path / "learn-the-code",
                  notebook_path / "use-cases" / "Ice_Sheets",
                  notebook_path / "use-cases" / "Lakes_and_Rivers",
                  notebook_path / "use-cases" / "Seasonal_Snow_Accumulation",
                  notebook_path / "use-cases" / "Soil_Moisture",
                  notebook_path / "use-cases" / "Tides"]

if __name__ == "__main__":
    move_forward = input(f"Is this the directory you would like to remove data from?: {notebook_path} (y/n)")
    if move_forward == "y":
        for path in paths_to_clear:
            os.chdir(path)
            remove_items()
# Remove the item
