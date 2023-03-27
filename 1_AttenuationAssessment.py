""" 2022.11.09, by kexin
Attenuation Assessment Algorithm Tested with Phantom Data 
    - Phantom Datasheet: https://www.universalmedicalinc.com/mwdownloads/download/link/id/594
    - Including Functions:
        - Single Frequency Attenuation Assessment
        - Multi Frequency Attenuation Assessment
    - Required Sub-functions:
        - Read pgm 
        - RF data to Intensity
        - AC Value calculation
"""
import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from lib.pgm_folder import ParentFolderTagMg, PgmFolder, PgmFolderTagMg
from lib.attenuation import calACValue, singleFreqAttenuationAssessment, multiFreqAttenuationAssessment
from lib.utility.path import datetimeChangingFolder

# Attenuation Constant from https://www.universalmedicalinc.com/mwdownloads/download/link/id/594
# low: 0.07 dB/cm-MHz,  high: 0.5 dB/cm-MHz
goalAttenuations = {"low": 0.07, "high": 0.5}

# Path handling
rootPath = ParentFolderTagMg(Path('data').joinpath("1-attenuation").joinpath('5 Sep Attenuation'))
# rootPath.ls()
imgFolderName = "1-attenuation-assessment"
imgPath = Path.cwd().joinpath("results").joinpath(imgFolderName)
imgPath = datetimeChangingFolder(imgPath)

# data folder manager
assert rootPath.dirs is not None
fdMg = PgmFolderTagMg(rootPath.dirs)
tags = ["5mhz", "7.5mhz", "9.6mhz", "11.4mhz", "5cm", "4cm", "high", "low"]
fdMg.addTagsByFolderName(tags)
fdMg.ls()

# Single Freq Attenuation Assessment
#   - for each single frequency in low and high attenuation area
#   - with testing at idx 120 and idx half row
#   - and with different combinations of blockSize 10,20,50
#   - save all the figures
imgSinglePath = imgPath.joinpath("Single Frequency")
imgSinglePath.mkdir(parents=True, exist_ok=True)

for atArea in ["low", "high"]:
    for fd in fdMg.tagGroup[atArea]:
        pgmFile = fd.readRandomPgm(printOut=False)
        acValue = calACValue(pgmFile.env, method="average")

        fig, ax = plt.subplots(1)
        pgmFile.showBMode(ax=ax)  # type: ignore
        figName = f"Single_b_mode_{pgmFile.path.name}_{pgmFile.fileName}.png"
        fig.savefig(imgSinglePath.joinpath(figName))  # type: ignore

        startIdx = 104
        halfIdx = int(acValue.shape[0] / 2)  # Probe related parameter

        for idx in [startIdx, halfIdx]:
            for blockSize in [1, 10, 20, 50]:
                acReal = acValue[idx:]

                figPathName = imgSinglePath.joinpath(
                    f"{atArea}_{pgmFile.frequency:.1f}mHz_idx{idx}_blkSize{blockSize}_{pgmFile.fileName}.png")
                assert pgmFile.frequency is not None and pgmFile.depthCm is not None
                attenuation = singleFreqAttenuationAssessment(pgmFile.frequency,
                                                              acReal,
                                                              pgmFile.depthCm,
                                                              goalAttenuation=goalAttenuations[atArea],
                                                              blockSize=blockSize,
                                                              figPathName=figPathName)
                print(f"{atArea}: {fd.folderName}\t{pgmFile.fileName}"
                      f"\tidx {idx}\tblock size {blockSize}\tmean Attenuation: {np.mean(attenuation):.2f}")
        plt.close('all')
print("Done")

# Multi Freq Attenuation Assessment
imgMultiPath = imgPath.joinpath("Multi Frequency")
imgMultiPath.mkdir(parents=True, exist_ok=True)

for atDepth in ["5cm", "4cm"]:
    for atArea in ["high", "low"]:
        depth = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", atDepth)[0])
        subFolderGroupList: list[PgmFolder] = fdMg.findByTags([atDepth, atArea])
        if len(subFolderGroupList) == 2:
            # get mHz
            mHzList = []
            for fd in subFolderGroupList:
                for t in fd.tags:
                    if "mhz" in t:
                        mHzList.append(float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", t)[0]))

            # calc AC value
            fdFreq0: PgmFolder = subFolderGroupList[0]
            fdFreq1: PgmFolder = subFolderGroupList[1]
            pgmFile0 = fdFreq0.readRandomPgm(printOut=False)
            pgmFile1 = fdFreq1.readRandomPgm(printOut=False)
            acValue0 = calACValue(pgmFile0.env, method="average")
            acValue1 = calACValue(pgmFile1.env, method="average")

            # plot b-mode
            fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2)
            pgmFile0.showBMode(ax=ax0)
            ax0.set_title(f"{mHzList[0]}mHz_{pgmFile0.fileName}")
            pgmFile1.showBMode(ax=ax1)
            ax1.set_title(f"{mHzList[1]}mHz_{pgmFile1.fileName}")
            fig.suptitle(f"B mode - Attenuation Area: {atArea} - Depth: {depth} cm")
            figName = f"Multi_b_mode_{atArea}_{depth}_" \
                      f"{mHzList[0]}Mhz_{pgmFile0.fileName}_{mHzList[1]}Mhz_{pgmFile1.fileName}.png"
            fig.savefig(imgMultiPath.joinpath(figName))  # type: ignore

            # start Multi - Frequency Attenuation Assessment
            startIdx = 104
            halfIdx = min(int(acValue0.shape[0] / 2), int(acValue0.shape[0] / 2))  # Probe related parameter

            for idx in [startIdx, halfIdx]:
                for blockSize in [1, 10, 20, 50]:
                    acReal0 = acValue0[idx:]
                    acReal1 = acValue1[idx:]
                    assert len(acReal0) == len(acReal1)  # currently only support same size ac value

                    figPathName = imgMultiPath.joinpath(
                        f"{atArea}_{mHzList[0]}Mhz_{mHzList[1]}Mhz_idx{idx}_"
                        f"blkSize{blockSize}_{pgmFile0.fileName}_{pgmFile1.fileName}.png")
                    attenuation = multiFreqAttenuationAssessment(freqs=mHzList,
                                                                 acDbs=[acReal0, acReal1],
                                                                 depth=depth,
                                                                 goalAttenuation=goalAttenuations[atArea],
                                                                 blockSize=blockSize,
                                                                 figPathName=figPathName)
        else:
            print("Current only support Multi-frequency Attenuation Assessment algorithm for 2 frequencies")
print("Done")
