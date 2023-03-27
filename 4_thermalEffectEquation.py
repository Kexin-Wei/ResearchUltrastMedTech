""" 2022.11.22, by Kexin
Estimate the thermal effect of one single point in the surgery model in sweep mode
under the influence of the surrounding points
    - Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcnFMptyltJkKYTW1GhhLkvEb
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

from lib.hifu_us_field import read_xlsx, findDbArea, egoThermalIntegral, neighbourThermalIntegral

HIFU_TYPE = 1001
SCAN_PLAN = "xy"  # "xy", "xz", or "yz"
DATA_TYPE = "vpp"  # "vpp" or "vrms"
DATE = 20221124

# Model Data
LESION_WIDTH = 2.5  # mm
LESION_HEIGHT = 5  # mm
POINT_SPACING = 4  # mm
LAYER_SPACING = 2.2  # mm
N_NEIGHBOUR = 6
PACKING_TYPE = "hexagonal"
DB_VALUE = -26

# 1. Get integral area according to the db value -26  or -6
scanArray, xPoints, yPoints, xSpacing, ySpacing = read_xlsx(hifuType=HIFU_TYPE,
                                                            date=DATE,
                                                            scanPlan=SCAN_PLAN,
                                                            dataType=DATA_TYPE)

db26Area, centerIj, radius = findDbArea(scanArray, dbValue=DB_VALUE)
fig, ax = plt.subplots()
ax.imshow(db26Area, cmap='gray')
ax.plot([centerIj[0]], [centerIj[1]], marker='s', markerfacecolor='r', markeredgecolor='r')
plt.title(f"dB {DB_VALUE} area of the Scan")
plt.show()

# 2. Calc self thermal estimate
egoThermal = egoThermalIntegral(db26Area, LESION_WIDTH / 2, centerIj, [xSpacing, ySpacing], showFlag=True)

# 3. Calc neighbour thermal estimate
neighbourThermalTotal, singleNeighbourThermal = neighbourThermalIntegral(db26Area,
                                                                         LESION_WIDTH / 2,
                                                                         centerIj, [xSpacing, ySpacing],
                                                                         N_NEIGHBOUR,
                                                                         showFlag=True)
thermal = egoThermal + neighbourThermalTotal
print(f"Total thermal in one period is {thermal:.2f}"
      f"\n\t - egoThermal is {egoThermal:.2f} at {egoThermal / thermal * 1e2:.2f}%"
      f"\n\t - neighbourThermal of {N_NEIGHBOUR} in {PACKING_TYPE} is {neighbourThermalTotal:.2f}"
      f" at {neighbourThermalTotal / thermal * 1e2:.2f}%, single neighbour thermal is {singleNeighbourThermal:.2f}")
print("done")
