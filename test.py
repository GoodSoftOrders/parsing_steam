import os
from pathlib import Path

path_dir = Path(__file__).parent
path_file = "{}{}{}{}".format(path_dir, os.sep, 'name', 'data')

print(path_file)