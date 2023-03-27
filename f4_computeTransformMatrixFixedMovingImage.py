"""
Compute the ground truth (the transform matrix between two recorded DICOM images) of the ShangTao's 2D medical images
registration algorithm
- Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcnYxK1CgcwHVO1BBz4wfywph
"""

from pathlib import Path
import numpy as np

from lib.folder import FolderMg
from lib.image_registration import getTransformMatrixFromFixedMoving


def methodVerify():
    testMode = 2  # 1, or 2, or 3
    transformType = "image"  # "probe" or "image, "probe" means T_probe_to_world, "image" means T_image_prob_to_world
    # more about coordinates can refer to https://ultrastmedtech.feishu.cn/wiki/wikcn4y7AeoUxfYHlvXXOKTrFKd

    testModeDict = {2: "2_rotation",
                    3: "3_translation_rotation"}

    testDataFolder = Path("data").joinpath("f4-fixed-moving-images", testModeDict[testMode])
    dataMg = FolderMg(testDataFolder)
    dataMg.ls()
    assert dataMg.files is not None
    if testMode == 2:
        transformMatrix = getTransformMatrixFromFixedMoving(dataMg.files[0], dataMg.files[1], readType=transformType)
        print(transformMatrix)
        print(f"this should be a rotation matrix with 3 degree")

    if testMode == 3:
        transformMatrix = getTransformMatrixFromFixedMoving(dataMg.files[0], dataMg.files[1], readType=transformType)
        print(transformMatrix)
        print(f"should have translation with z 5mm")

        transformMatrix = getTransformMatrixFromFixedMoving(dataMg.files[0], dataMg.files[2], readType=transformType)
        print(transformMatrix)
        print(f"should have translation with z 0mm")

        transformMatrix = getTransformMatrixFromFixedMoving(dataMg.files[2], dataMg.files[3], readType=transformType)
        print(transformMatrix)
        print(f"A rotation + translation")


def getKidneyTransform():
    # data source: https://ultrastmedtech.feishu.cn/wiki/wikcnshQqwJm17JlOu5s0ec6Hld
    np.set_printoptions(precision=3, suppress=True)
    testDataFolder = Path("data").joinpath("f4-fixed-moving-images", "4_realKidneyData")
    groupImageTags = [  # 1067, 1260, 1260, 1475, 1475, 1592,
        1795, 1809, 1809, 1993, 1993, 2075, 2075, 2119, 2119, 2178]
    dataMg = FolderMg(testDataFolder)
    # dataMg.ls()
    groupImages = []

    assert dataMg.files is not None
    for tag in groupImageTags:
        for f in dataMg.files:
            if f.name.find(str(tag)) > 0:
                groupImages.append(f)
    fixedImagePaths = groupImages[0::2]
    movingImagePaths = groupImages[1::2]
    for idx in range(len(fixedImagePaths)):
        transformMatrix = getTransformMatrixFromFixedMoving(fixedImagePaths[idx], movingImagePaths[idx],
                                                            readType="image")
        print(f"\n - Transform matrix between{fixedImagePaths[idx].name} and {movingImagePaths[idx].name}\n",
              transformMatrix)


# methodVerify()
getKidneyTransform()
print("done")
