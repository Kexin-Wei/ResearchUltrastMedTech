# test rhino3dm for nubrs model, by kx, 2023.04.21

import rhino3dm
from pathlib import Path

# import stl file
fileName = Path("data").joinpath("test-model-files", "after_extract.stl")
# read stl file
# model = rhino3dm.File3dm.Read(str(fileName))
model = rhino3dm.File3dm()
writePath = Path("data").joinpath("test-model-files", "test.3dm")


for i in range(5):

    ### Define Geometry
    pt = rhino3dm.Point3d(i, i, i)
    pc = rhino3dm.PointCloud()
    pc.Add(pt)
    print(pt)
    print(type(pt))

    ### Add Object
    model.Objects.AddPointCloud(pc)

model.Write(str(writePath), 6)
# display the model
