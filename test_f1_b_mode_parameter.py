# test individual pgm file
from lib.pgm import PGMFile
from lib.b_mode_gui import BModeWindow

pgmFile = PGMFile("D:/treatment_data/05_12_10_32_25_model3_fixed/3.pgm")
bModeWindow = BModeWindow(pgmFile=pgmFile)
