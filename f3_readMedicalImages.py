"""
simple functions to open DICOM files and NRRD files
"""
import pydicom
import nrrd
from pathlib import Path

from lib.folder import FolderMg

testDataFolder = Path("data").joinpath("f3-medical-images")
dataMg = FolderMg(testDataFolder)
dataMg.ls()

# read a dicom file
assert dataMg.files is not None
for f in dataMg.files:
    if f.suffix.lower() == ".dcm":
        print(f.name)
        ds = pydicom.dcmread(f)
        break

# read a nrrd file
for f in dataMg.files:
    if f.suffix.lower() == ".nrrd":
        print(f.name)
        readData, header = nrrd.read(f)
        break

ds = pydicom.dcmread(testDataFolder.joinpath("Patient_13_Surgery_14_Timestamp_3574.51.dcm"))
print("done")
