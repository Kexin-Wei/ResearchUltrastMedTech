from lib.pgm import PGMFile
import numpy as np
import matplotlib.pyplot as plt

pgmFile = PGMFile(r"data/test-pgm-files/4-hifu.pgm")
# pgmFile.showBMode()
pgmFile.getStftMagnitudeDb()
pgmFile.getStftMagnitudeDbMean()

assert isinstance(pgmFile.stftMagnitudeDb, np.ndarray) and isinstance(pgmFile.stftMagnitudeDbMean, np.ndarray)
print(pgmFile.stftMagnitudeDb.shape)
print(pgmFile.stftMagnitudeDbMean.shape)

# pgmFile.showStft(saveFig=True)
pgmFile.hifuScanLine = np.array([102, 117]).astype(int)  # type: ignore
pgmFile.getStftMagnitudeDbScanlineMean()

assert pgmFile.fsMhz is not None
hifuFreq = 1.3
scanFreq = pgmFile.fsMhz / 2
nHarmonics = np.floor(scanFreq / hifuFreq).astype(int)
nFFT = pgmFile.stftMagnitudeDbMean.shape[0]
harmonicFreqSectionIndexes = (nFFT * nHarmonics * hifuFreq /
                              scanFreq) * np.c_[np.arange(nHarmonics) + 0.25,
                                                (np.arange(nHarmonics) + 1) - 0.25] / nHarmonics
minRange = np.min(np.absolute(harmonicFreqSectionIndexes[:, 0] - harmonicFreqSectionIndexes[:, 1])).astype(int)
harmonicFreqSectionIndexes = np.vstack(
    (harmonicFreqSectionIndexes[:, 0], harmonicFreqSectionIndexes[:, 0] + minRange)).astype(int).T
harmonicFreqSectionIndexes = np.linspace(harmonicFreqSectionIndexes[:, 0],
                                         harmonicFreqSectionIndexes[:, 1],
                                         num=minRange,
                                         dtype=np.int32)

stftMagnitudeScanlineMeanDenoise = pgmFile.stftMagnitudeDbScanlineMean
scanLineBbnIntervals = stftMagnitudeScanlineMeanDenoise[harmonicFreqSectionIndexes]
pgmFile.bbnIntervals = scanLineBbnIntervals.mean(axis=0)

f, ax = plt.subplots(1, figsize=(12, 6))
ax.plot(stftMagnitudeScanlineMeanDenoise, linewidth=1) # type: ignore
for i in range(harmonicFreqSectionIndexes.shape[1]):
    x = harmonicFreqSectionIndexes[:, i]
    y = stftMagnitudeScanlineMeanDenoise[x]
    ax.plot(x, y, "^", markersize=4)# type: ignore
ticks = np.round(np.arange(1, nHarmonics + 1) * nFFT * hifuFreq / scanFreq, decimals=1)
labels = np.round(np.arange(1, nHarmonics + 1) * hifuFreq, decimals=1)
ax.set_xticks(ticks=ticks, labels=labels)# type: ignore
ax.grid()# type: ignore
ax.set_ylim(ymin=0)# type: ignore
ax.set_xlim(xmin=0)# type: ignore
plt.show()
print("Done")