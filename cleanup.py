import os

# read the temp data that has video paths
with open("tempdata.txt", "r") as f:
    paths = f.readlines()

os.remove(paths[0].strip())  # remove the first path (the large video
os.rename(paths[1].strip(), paths[0].strip())  # rename the second path to original name
os.remove("tempdata.txt")