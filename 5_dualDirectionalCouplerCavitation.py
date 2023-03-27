"""2022.11.24, by Kexin
Analyse whether the feedback of the transducer side in the dual directional coupler
can be used as simple Passive Cavitation Detector (PCD)
    - Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcnOiiR3pH9HWGvUiffjVgwLc
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from lib.folder import FolderMg
from lib.oscilloscope_read_file import readTxt

dateTag = "22Nov"  # need to change according to data
sampleTime = 0.01  # unit: s

dataPath = Path("data").joinpath("5-coupler").joinpath(dateTag)
dataMg = FolderMg(dataPath)
dataMg.ls()
assert dataMg.dirs is not None
for folder in dataMg.dirs:
    tempFolderMg = FolderMg(folder)
    dataFile = tempFolderMg.getRandomFile()
    couplerData = readTxt(dataFile.absolute())

    dataFft = np.fft.fft(couplerData[:, 1])
    fs = couplerData.shape[0] / sampleTime / 1e6  # sample frequency: MHz
    assert fs > 6  # Fs too small, not enough to have an accurate bbn

    fig, ax = plt.subplots()
    ax.plot(couplerData[:, 0], couplerData[:, 1])
    fig.show()
    break
