#!/usr/bin/env python
import os
import os.path
import glob
import argparse
import json

parser = argparse.ArgumentParser(description="List file stat results")
parser.add_argument("dirs", nargs="+", help="target dirs.")
args = parser.parse_args()

for dir_pattern in args.dirs:
    for d in glob.glob(dir_pattern):
        dir_name = os.path.split(os.path.abspath(os.path.join(d, ".")))[-1]
        out = f"{dir_name}-stat.json"
        files_dict = {}
        out_dict = { "dir": dir_name, "files": files_dict }
        for file in os.listdir(d):
            stat_dict = {}
            stat_result = os.stat(os.path.join(d, file))
            for attr in dir(stat_result):
                if attr.startswith('st_'):
                    stat_dict[attr] = stat_result.__getattribute__(attr)
            files_dict[file] = stat_dict
        with open(out, 'w') as f:
            json.dump(out_dict, f, indent=2)

