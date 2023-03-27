"""
Processed folders used to be part of the folders inside a parent folder (e.g. DataAcq)
    - this parent folder will be the rootPath
    - the needed folders should be added into the list with names
"""
from pathlib import Path

from lib.pgm_folder import ParentFolderTagMg

# !!! need to change before running
rootPath = Path("D:/treatment_data")
imageRootFolderPath = Path("D:/treatment_data/RF images")

folderList = ["06_12_10_03_21_calibration1_fixed_mode"]

pgmFolderManager = ParentFolderTagMg(rootPath)
pgmFolderManager.createNewFolderList(folderList)
pgmFolderManager.ls()

# save b-mode
assert pgmFolderManager.nDirs is not None
for ithFolder in range(pgmFolderManager.nDirs):
    ithPgmFolder = pgmFolderManager.readPgmFolder(ithFolder)
    ithPgmFolder.saveBModes(imageRootFolderPath=imageRootFolderPath,
                            lowerDisplayRangeDb=40, upperDisplayRangeDb=80,
                            replace=False)
