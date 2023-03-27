"""
Short Time Fourier Transfer (STFT) Algorithm to Find the Broad-band Noise (BBN)
- Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcn5EJ1VcxNYMDB401qnQ5Aeb

Background:
1. BBN can be found and extracted between fundamental  and harmonics
2. STFT should be used in continuous signal, here is each scanline in the RF data

Test files:
- baseline x2
- hifu x2
- non hifu x2
"""
from lib.pgm_folder import PgmFolder
from lib.calibration import CalibrationManager

# !!! need to change before running
pgmFolder = PgmFolder("D:/treatment_data/05_12_10_32_25_model3_fixed")
pgmFolder.ls()

calibrationMg = CalibrationManager()
calibrationMg.changeSetting(baseLineUpdateFreq=10)

idxTestMax = 80
assert pgmFolder.nFile is not None and pgmFolder.files is not None
for ithPgm in range(pgmFolder.nFile):
    bbn = calibrationMg.getPgmCavitationBbn(pgmFolder.files[ithPgm])
    if ithPgm >= idxTestMax:
        break
print("done")
