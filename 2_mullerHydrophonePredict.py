"""
Get the relationship between Voltage and Pressure in oil as one of the Mueller Hydrophone Characteristics
 - Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcnsCxxGvq26Eae6v5d61zUsc
 - Print Out Order Following: https://numpy.org/doc/stable/reference/generated/numpy.polyfit.html
   as p(x) = p[0] * x**deg + ... + p[deg]
created by Kexin, 20221103
"""
#%% Import
import numpy as np
import matplotlib.pyplot as plt

#%% Oil 
powerInput = np.array([4, 16, 32, 48, 64, 80, 96, 128])
electricPower = powerInput*6
acousticPower = electricPower*0.51 

#%% Peak Value Read in Ocsilloscop
voltageNegRead = np.array([-24.8, -42.2, -56, -62, -68, -72, -76, -80])
voltagePosRead = np.array([34.4, 79.2, 132, 172, 202, 226, 248, 272])

#%% Pressure transferred from Vendor
pressureNeg = voltageNegRead/12.8
pressurePos = voltagePosRead/12.8

#%% Show Data
plt.figure()
plt.plot(acousticPower,pressureNeg,'.')
plt.plot(acousticPower,pressurePos,'.')
plt.show(block = False)

#%% fit polynormial
## Degree 2
pNeg = np.polyfit(acousticPower,pressureNeg,2)
pPos = np.polyfit(acousticPower,pressurePos,2)
print(f"Negative Fit Parameters are: {pNeg}")
print(f"Positive Fit Parameters are: {pPos}")
fNeg = np.poly1d(pNeg)
fPos = np.poly1d(pPos)

plt.figure()
acousticPowerRange = np.array([np.floor(acousticPower.min()/10)*10, np.ceil(acousticPower.max()/10)*10])
xp = np.linspace(acousticPowerRange[0],acousticPowerRange[-1],500)
plt.plot(acousticPower,pressureNeg,'.',label = "Negative Peak")
plt.plot(acousticPower,pressurePos,'.',label = "Positive Peak")
plt.plot(xp,fNeg(xp),'-',label = "Negative Fit")
plt.plot(xp,fPos(xp),'-',label = "Positive Fit")
plt.legend()
plt.show()

print("Done")
