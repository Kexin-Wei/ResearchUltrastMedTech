### config.ini, Focus Point Position 焦点位置.txt, Saved Position 保存位置.txt on same level as this file
### Update config file

import sys, os.path, time
import gclib
import pyvisa as visa
import logging
import configparser
import numpy as np
import pylab as plt
from datetime import datetime
import xlsxwriter

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QPushButton, QLineEdit, QDesktopWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont

cmdList = []


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super(QTextEditLogger, self).__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.setFont(window.fontNormal)


class c_cmdList(QObject):
    def __init__(self, activeCmdList):
        super().__init__()
        self.activeCmdList = activeCmdList

    finished = pyqtSignal()
    updatePos = pyqtSignal()
    log = pyqtSignal(str, str)
    initialiseEnd = pyqtSignal()

    def run(self):
        initialising = False
        while self.activeCmdList == True:
            if initialising == True:
                try:
                    initialising = float(c1("initLS = ?"))
                except:
                    pass
                if initialising == 0:
                    initialising = False
                    self.initialiseEnd.emit()
            if len(cmdList) > 0:
                MotorStateA = '{0:08b}'.format(int(c1("TSA")))
                MotorStateB = '{0:08b}'.format(int(c1("TSB")))
                MotorStateC = '{0:08b}'.format(int(c1("TSC")))
                if MotorStateA[0] == MotorStateB[0] == MotorStateC[0] == "0":
                    self.log.emit('Galil: ' + cmdList[0], 'debug')
                    c1(cmdList[0])
                    if cmdList[0] == "XQ #midpt, 3":
                        initialising = True
                    cmdList.remove(cmdList[0])
                else:
                    self.updatePos.emit()
            else:
                self.updatePos.emit()
            time.sleep(0.01)
        self.finished.emit()


class c_saveWaveform(QObject):
    def __init__(self):
        super().__init__()

    finished = pyqtSignal()
    log = pyqtSignal(str, str)
    plot = pyqtSignal(np.ndarray, np.ndarray, str)

    def saveWaveform(self):
        self.log.emit('Saving Waveform', 'info')
        boxPerScreen = 10  # not sure if it will change with other oscilloscope
        Hscale = float(window.scope.query("horizontal:main:scale?"))
        recDuration = Hscale * boxPerScreen
        recLen = float(window.scope.query("horizontal:recordlength?"))  # points per screen
        window.scope.write('header 0')
        window.scope.write('data:encdg RIBINARY')
        window.scope.write('data:source CH1')  # channel
        window.scope.write('data:start 1')  # first sample
        window.scope.write("data:stop " + str(recLen))
        window.scope.write('wfmpre:byt_nr 8')  # 1 byte per sample
        rawData = window.scope.query_binary_values('curve?', datatype='b', container=np.array)
        # retrieve scaling factors
        vscale = float(window.scope.query('wfmpre:ymult?'))  # volts / level
        voff = float(window.scope.query('wfmpre:yzero?'))  # reference voltage
        vpos = float(window.scope.query('wfmpre:yoff?'))  # reference position (level)
        # process data
        scaledTime = []
        scaledVolt = []
        # vertical (voltage)
        unscaledVolt = np.array(rawData, dtype='double')  # data type conversionnn
        scaledVolt = (unscaledVolt - vpos) * vscale + voff
        # horizontal (time)
        scaledTime = np.linspace(0, recDuration, len(scaledVolt))
        # save as .csv format
        fullFilename = window.createFile(otherSettings['saveLocationData'], "Waveform_波形")
        file = open(fullFilename + '.csv', 'w')
        file.write("Time/s,Volts/V\n")
        for i in range(0, len(scaledVolt)):
            file.write(str(scaledTime[i]) + ',' + str(scaledVolt[i]) + '\n')
        self.log.emit('Waveform saved in' + fullFilename, 'info')
        file.close()
        self.plot.emit(scaledTime, scaledVolt, fullFilename)
        self.finished.emit()


class c_scanXYZ(QObject):
    def __init__(self, activeScanXYZ, fullFilename, axis, locationsAxis0, locationsAxis1,
                 locationsAxis2):  # axis=[axis0,axis1,axis2]
        super().__init__()
        self.activeScanXYZ = activeScanXYZ
        self.fullFilename = fullFilename
        self.locationsAxis0 = locationsAxis0
        self.locationsAxis1 = locationsAxis1
        self.locationsAxis2 = locationsAxis2
        self.axis = axis

    finished = pyqtSignal()
    log = pyqtSignal(str, str)

    def recordData(self):
        # set values based on axis
        fpAxis = [0, 0, 0]
        for n in range(0, len(self.axis)):
            if self.axis[n] == 'x':
                fpAxis[n] = window.fpXmm
            elif self.axis[n] == 'y':
                fpAxis[n] = window.fpYmm
            elif self.axis[n] == 'z':
                fpAxis[n] = window.fpZmm
        unitAxis = [0, 0, 0]
        for n in range(0, len(self.axis)):
            if self.axis[n] == 'x':
                unitAxis[n] = window.unitA
            elif self.axis[n] == 'y':
                unitAxis[n] = window.unitB
            elif self.axis[n] == 'z':
                unitAxis[n] = window.unitC
        galilAxis = [0, 0, 0]
        for n in range(0, len(self.axis)):
            if self.axis[n] == 'x':
                galilAxis[n] = 'A'
            elif self.axis[n] == 'y':
                galilAxis[n] = 'B'
            elif self.axis[n] == 'z':
                galilAxis[n] = 'C'
        self.log.emit('Scan Start', 'info')
        # create xlsx file
        wbVpp = xlsxwriter.Workbook(self.fullFilename + '_Vpp.xlsx')
        wbVrms = xlsxwriter.Workbook(self.fullFilename + '_Vrms.xlsx')
        # start running
        # measurement 1: Vpp
        window.scope.write("measurement:meas1:source ch1")
        window.scope.write("measurement:meas1:type pk2pk")
        # measurement 2: Vrms
        window.scope.write("measurement:meas2:source ch1")
        window.scope.write("measurement:meas2:type rms")
        for axis2 in self.locationsAxis2:
            if self.activeScanXYZ == True:
                sheetname = round((axis2 - fpAxis[2]), 2)
                wsVpp = wbVpp.add_worksheet(self.axis[2] + "=" + str(sheetname))
                wsHeader0 = [0, " ", "FP", " ", " "]
                wsHeader1 = ["Vpp/V", " ", fpAxis[0], fpAxis[1], fpAxis[2]]
                if len(self.locationsAxis2) > 1:
                    rangeTemp = len(self.axis)
                else:
                    rangeTemp = len(self.axis) - 1
                for n in range(0, rangeTemp):
                    if self.axis[n] == 'x':
                        wsHeader0.append("X Range/mm")
                        wsHeader1.append(window.xRange_float)
                    elif self.axis[n] == 'y':
                        wsHeader0.append("Y Range/mm")
                        wsHeader1.append(window.yRange_float)
                    elif self.axis[n] == 'z':
                        wsHeader0.append("Z Range/mm")
                        wsHeader1.append(window.zRange_float)
                for n in range(0, rangeTemp):
                    if self.axis[n] == 'x':
                        wsHeader0.append("X Interval/mm")
                        wsHeader1.append(window.XYInterval)
                    elif self.axis[n] == 'y':
                        wsHeader0.append("Y Interval/mm")
                        wsHeader1.append(window.XYInterval)
                    elif self.axis[n] == 'z':
                        wsHeader0.append("Z Interval/mm")
                        wsHeader1.append(window.ZInterval)
                wsVpp.write_row(0, 0, wsHeader0)
                wsVpp.write_row(1, 0, wsHeader1)
                wsVpp.write(2, 0, (self.axis[0] + self.axis[1] + '/mm'))
                wsVpp.write_column(3, 0, self.locationsAxis1 - fpAxis[1])
                wsVpp.write_row(2, 1, self.locationsAxis0 - fpAxis[0])
                wsVrms = wbVrms.add_worksheet(self.axis[2] + "=" + str(sheetname))
                wsHeader1[0] = "Vrms/V"
                wsVrms.write_row(0, 0, wsHeader0)
                wsVrms.write_row(1, 0, wsHeader1)
                wsVrms.write(2, 0, (self.axis[0] + self.axis[1] + '/mm'))
                wsVrms.write_column(3, 0, self.locationsAxis1 - fpAxis[1])
                wsVrms.write_row(2, 1, self.locationsAxis0 - fpAxis[0])
                wsRow = 3
                for axis1 in self.locationsAxis1:
                    if self.activeScanXYZ == True:
                        wsCol = 1
                        # set motor speed to scanning
                        c1("SPA = @ABS[unitA*spS]; SPB = @ABS[unitB*spS]; SPC = @ABS[unitC*spS]")
                        c1("ACA = @ABS[unitA*acS]; ACB = @ABS[unitB*acS]; ACC = @ABS[unitC*acS]")
                        c1("DCA = @ABS[unitA*dcS]; DCB = @ABS[unitB*dcS]; DCC = @ABS[unitC*dcS]")
                        for axis0 in self.locationsAxis0:
                            if self.activeScanXYZ == True:
                                countsAxis0 = axis0 * unitAxis[0]
                                countsAxis1 = axis1 * unitAxis[1]
                                countsAxis2 = axis2 * unitAxis[2]
                                cmdList.append("PA" + str(galilAxis[0]) + "=" + str(countsAxis0) + ";PA" + str(
                                    galilAxis[1]) + "=" + str(countsAxis1) + ";PA" + str(galilAxis[2]) + "=" + str(
                                    countsAxis2) + ";SHABC;BGABC")
                                posAxis = [window.xPos, window.yPos, window.zPos]
                                while abs(posAxis[0] - axis0) > 0.01 or abs(posAxis[1] - axis1) > 0.01 or abs(
                                        posAxis[2] - axis2) > 0.01:
                                    window.updatePosLbl()
                                    for n in range(0, len(self.axis)):
                                        if self.axis[n] == 'x':
                                            posAxis[n] = window.xPos
                                        elif self.axis[n] == 'y':
                                            posAxis[n] = window.yPos
                                        elif self.axis[n] == 'z':
                                            posAxis[n] = window.zPos
                                    # print(abs(posAxis[0]-axis0),abs(posAxis[1]-axis1),abs(posAxis[2]-axis2))
                                    time.sleep(0.01)
                                time.sleep(float(scanningParameters['delayTime']))
                                print(posAxis)
                                # Record Data
                                Vpp = float(window.scope.query("measurement:meas1:value?"))
                                Vrms = float(window.scope.query("measurement:meas2:value?"))
                                if Vpp == 9.9E37:
                                    Vpp = 0
                                if Vrms == 9.9E37:
                                    Vrms = 0
                                wsVpp.write(wsRow, wsCol, Vpp)
                                wsVrms.write(wsRow, wsCol, Vrms)
                                wsCol += 1
                            else:
                                break
                        wsRow += 1
                        # set motor speed for movement to next row
                        c1("SPA = @ABS[unitA*spN]; SPB = @ABS[unitB*spN]; SPC = @ABS[unitC*spN]")
                        c1("ACA = @ABS[unitA*acN]; ACB = @ABS[unitB*acN]; ACC = @ABS[unitC*acN]")
                        c1("DCA = @ABS[unitA*dcN]; DCB = @ABS[unitB*dcN]; DCC = @ABS[unitC*dcN]")
                        # self.log.emit('z='+str(window.XposRelFP)+', y='+str(window.YposRelFP)+' done','info')
                    else:
                        break
            else:
                # self.log.emit('stop Pressed', 'warning')
                break
        wsVpp.write(0, wsCol - 1,
                    '0')  # add additional 0 at start of last col if not matlab readmatrix will have issues
        wsVrms.write(0, wsCol - 1, '0')
        wbVpp.close()
        wbVrms.close()
        self.log.emit('Scan Done', 'info')
        self.log.emit('Total scan time' + str(datetime.now() - window.scanStart), 'info')
        self.finished.emit()


class Display(QWidget):
    def __init__(self):
        super(Display, self).__init__()
        # Define fonts
        self.fontNormal = QFont('DengXian', 11)
        self.fontNormal.setBold(False)
        self.fontHeader = QFont('DengXian', 12)
        self.fontHeader.setBold(True)

        # Define linear stage parameters
        self.XLimMin = float(linearStage['rangeAMin'])
        self.XLimMax = float(linearStage['rangeAMax'])
        self.YLimMin = float(linearStage['rangeBMin'])
        self.YLimMax = float(linearStage['rangeBMax'])
        self.ZLimMin = float(linearStage['rangeCMin'])
        self.ZLimMax = float(linearStage['rangeCMax'])
        self.unitA = float(linearStage['unitA'])
        self.unitB = float(linearStage['unitB'])
        self.unitC = float(linearStage['unitC'])
        self.xPos = 0.00
        self.yPos = 0.00
        self.zPos = 0.00

        # Setup UI
        self.setupUI()
        self.enableWidgets(False)
        # logging.info("PRESS START")

    def enableWidgets(self, enable):
        # Disable all inpupts/buttons
        # self.setDisabled(True)
        self.btn_start.setEnabled(not enable)
        self.btn_initialise.setEnabled(enable)
        self.btn_stop.setEnabled(enable)
        self.btn_moveFP.setEnabled(enable)
        self.inp_moveX.setEnabled(enable)
        self.inp_moveY.setEnabled(enable)
        self.inp_moveZ.setEnabled(enable)
        self.inp_X.setEnabled(enable)
        self.inp_Y.setEnabled(enable)
        self.inp_Z.setEnabled(enable)
        self.inp_xRange.setEnabled(enable)
        self.inp_yRange.setEnabled(enable)
        self.inp_zRange.setEnabled(enable)
        self.inp_xyInterval.setEnabled(enable)
        self.inp_zInterval.setEnabled(enable)

    def windowLocation(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = screen.height() - widget.height()
        self.move(x, 0)

    def setupUI(self):
        self.setWindowTitle("XYZ Linear Stage Control")
        self.setFixedWidth(850)

        # Widgets
        # Start, Stop, Exit Buttons
        self.btn_start = QPushButton("Start \n开始")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setFixedSize(200, 50)
        self.btn_start.setFont(self.fontNormal)

        self.btn_stop = QPushButton("Stop \n停止")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setFixedSize(350, 50)
        self.btn_stop.setFont(self.fontNormal)

        self.btn_exit = QPushButton("Exit \n退出")
        self.btn_exit.clicked.connect(self.exit)
        self.btn_exit.setFixedSize(200, 50)
        self.btn_exit.setFont(self.fontNormal)

        # Initialise, Set FP, Move to FP Buttons
        self.btn_initialise = QPushButton("Initialise \n初始化")
        self.btn_initialise.clicked.connect(self.initialise)
        self.btn_initialise.setFixedSize(200, 50)
        self.btn_initialise.setFont(self.fontNormal)

        self.btn_saveFP = QPushButton("Save as Focus Point \n保存焦点位置")
        self.btn_saveFP.clicked.connect(self.saveFP)
        self.btn_saveFP.setFixedSize(200, 50)
        self.btn_saveFP.setFont(self.fontNormal)

        self.btn_moveFP = QPushButton("Move to Focus Point: \n移动至焦点")
        self.btn_moveFP.clicked.connect(self.moveFP)
        self.btn_moveFP.setFixedSize(200, 50)
        self.btn_moveFP.setFont(self.fontNormal)

        file = open("Focus Point Position 焦点位置.txt", 'r')
        fpXCount = file.readline()
        fpYCount = file.readline()
        fpZCount = file.readline()
        file.close()

        fpXmm = round(float(fpXCount) / self.unitA, 2)
        fpYmm = round(float(fpYCount) / self.unitB, 2)
        fpZmm = round(float(fpZCount) / self.unitC, 2)
        FP = (fpXmm, fpYmm, fpZmm)

        self.lbl_FP = QLabel()
        self.lbl_FP.setText(str(FP))
        self.lbl_FP.setFixedSize(150, 50)
        self.lbl_FP.setFont(self.fontNormal)

        # Position Relative to FP
        self.lbl_posRelFP = QLabel()
        self.lbl_posRelFP.setText("Position Relative to FP 焦点相对位置/mm: (X , Y , Z)")
        self.lbl_posRelFP.setFixedHeight(50)
        self.lbl_posRelFP.setFont(self.fontNormal)

        # #X-axis Widgets
        self.lbl_xPos = QLabel()
        self.lbl_xPos.setText("X Pos 位置: " + str(self.xPos) + "mm")
        self.lbl_xPos.setFixedSize(175, 40)
        self.lbl_xPos.setFont(self.fontNormal)

        self.btn_moveXMinus1x = QPushButton("- 1.0x")
        self.btn_moveXMinus1x.clicked.connect(lambda: self.moveX(-1))
        self.btn_moveXMinus1x.setFixedSize(75, 40)
        self.btn_moveXMinus1x.setFont(self.fontNormal)

        self.btn_moveXMinus01x = QPushButton("- 0.1x")
        self.btn_moveXMinus01x.clicked.connect(lambda: self.moveX(-0.1))
        self.btn_moveXMinus01x.setFixedSize(75, 40)
        self.btn_moveXMinus01x.setFont(self.fontNormal)

        self.inp_moveX = QLineEdit()
        self.inp_moveX.setPlaceholderText("Move 移动/mm")
        self.inp_moveX.setFixedHeight(40)
        self.inp_moveX.setFont(self.fontNormal)

        self.btn_moveXPlus1x = QPushButton("+ 1.0x")
        self.btn_moveXPlus1x.clicked.connect(lambda: self.moveX(1))
        self.btn_moveXPlus1x.setFixedSize(75, 40)
        self.btn_moveXPlus1x.setFont(self.fontNormal)

        self.btn_moveXPlus01x = QPushButton("+ 0.1x")
        self.btn_moveXPlus01x.clicked.connect(lambda: self.moveX(0.1))
        self.btn_moveXPlus01x.setFixedSize(75, 40)
        self.btn_moveXPlus01x.setFont(self.fontNormal)

        self.btn_moveXMoveTo = QPushButton("Move to 移动至")
        self.btn_moveXMoveTo.clicked.connect(self.moveXMoveTo)
        self.btn_moveXMoveTo.setFixedSize(130, 40)
        self.btn_moveXMoveTo.setFont(self.fontNormal)

        # #Y-axis Widgets
        self.lbl_yPos = QLabel()
        self.lbl_yPos.setText("Y Pos 位置: " + str(self.yPos) + "mm")
        self.lbl_yPos.setFixedSize(175, 30)
        self.lbl_yPos.setFont(self.fontNormal)

        self.btn_moveYMinus1x = QPushButton("- 1.0x")
        self.btn_moveYMinus1x.clicked.connect(lambda: self.moveY(-1))
        self.btn_moveYMinus1x.setFixedSize(75, 40)
        self.btn_moveYMinus1x.setFont(self.fontNormal)

        self.btn_moveYMinus01x = QPushButton("- 0.1x")
        self.btn_moveYMinus01x.clicked.connect(lambda: self.moveY(-0.1))
        self.btn_moveYMinus01x.setFixedSize(75, 40)
        self.btn_moveYMinus01x.setFont(self.fontNormal)

        self.inp_moveY = QLineEdit()
        self.inp_moveY.setPlaceholderText("Move 移动/mm")
        self.inp_moveY.setFixedHeight(40)
        self.inp_moveY.setFont(self.fontNormal)

        self.btn_moveYPlus1x = QPushButton("+ 1.0x")
        self.btn_moveYPlus1x.clicked.connect(lambda: self.moveY(1))
        self.btn_moveYPlus1x.setFixedSize(75, 40)
        self.btn_moveYPlus1x.setFont(self.fontNormal)

        self.btn_moveYPlus01x = QPushButton("+ 0.1x")
        self.btn_moveYPlus01x.clicked.connect(lambda: self.moveY(0.1))
        self.btn_moveYPlus01x.setFixedSize(75, 40)
        self.btn_moveYPlus01x.setFont(self.fontNormal)

        self.btn_moveYMoveTo = QPushButton("Move to 移动至")
        self.btn_moveYMoveTo.clicked.connect(self.moveYMoveTo)
        self.btn_moveYMoveTo.setFixedSize(130, 40)
        self.btn_moveYMoveTo.setFont(self.fontNormal)

        # #Z-axis Widgets
        self.lbl_zPos = QLabel()
        self.lbl_zPos.setText("Z Pos 位置:  " + str(self.zPos) + "mm")
        self.lbl_zPos.setFixedSize(175, 40)
        self.lbl_zPos.setFont(self.fontNormal)

        self.btn_moveZMinus1x = QPushButton("- 1.0x")
        self.btn_moveZMinus1x.clicked.connect(lambda: self.moveZ(-1))
        self.btn_moveZMinus1x.setFixedSize(75, 40)
        self.btn_moveZMinus1x.setFont(self.fontNormal)

        self.btn_moveZMinus01x = QPushButton("- 0.1x")
        self.btn_moveZMinus01x.clicked.connect(lambda: self.moveZ(-0.1))
        self.btn_moveZMinus01x.setFixedSize(75, 40)
        self.btn_moveZMinus01x.setFont(self.fontNormal)

        self.inp_moveZ = QLineEdit()
        self.inp_moveZ.setPlaceholderText("Move 移动/mm")
        self.inp_moveZ.setFixedHeight(40)
        self.inp_moveZ.setFont(self.fontNormal)

        self.btn_moveZPlus1x = QPushButton("+ 1.0x")
        self.btn_moveZPlus1x.clicked.connect(lambda: self.moveZ(1))
        self.btn_moveZPlus1x.setFixedSize(75, 40)
        self.btn_moveZPlus1x.setFont(self.fontNormal)

        self.btn_moveZPlus01x = QPushButton("+ 0.1x")
        self.btn_moveZPlus01x.clicked.connect(lambda: self.moveZ(0.1))
        self.btn_moveZPlus01x.setFixedSize(75, 40)
        self.btn_moveZPlus01x.setFont(self.fontNormal)

        self.btn_moveZMoveTo = QPushButton("Move to 移动至")
        self.btn_moveZMoveTo.clicked.connect(self.moveZMoveTo)
        self.btn_moveZMoveTo.setFixedSize(130, 40)
        self.btn_moveZMoveTo.setFont(self.fontNormal)

        # XYZ Coordinates Inputs
        self.inp_X = QLineEdit()
        self.inp_X.setPlaceholderText("X/mm")
        self.inp_X.setFixedSize(100, 50)
        self.inp_X.setFont(self.fontNormal)

        self.inp_Y = QLineEdit()
        self.inp_Y.setPlaceholderText("Y/mm")
        self.inp_Y.setFixedSize(100, 50)
        self.inp_Y.setFont(self.fontNormal)

        self.inp_Z = QLineEdit()
        self.inp_Z.setPlaceholderText("Z/mm")
        self.inp_Z.setFixedSize(100, 50)
        self.inp_Z.setFont(self.fontNormal)

        # XYZ Move to Absolute/Relative Position Buttons
        self.btn_moveToAbs = QPushButton("Move to Absolute \n移动至绝对位置")
        self.btn_moveToAbs.clicked.connect(self.moveToAbs)
        self.btn_moveToAbs.setFixedSize(200, 50)
        self.btn_moveToAbs.setFont(self.fontNormal)

        self.btn_moveToRel = QPushButton("Move to Relative \n移动至焦点相对位置")
        self.btn_moveToRel.clicked.connect(self.moveToRel)
        self.btn_moveToRel.setFixedSize(200, 50)
        self.btn_moveToRel.setFont(self.fontNormal)

        # Autorun XYZ
        self.lbl_xRange = QLabel("X Range 范围/mm")
        self.lbl_xRange.setFont(self.fontNormal)
        self.lbl_yRange = QLabel("Y Range 范围/mm")
        self.lbl_yRange.setFont(self.fontNormal)
        self.lbl_zRange = QLabel("Z Range 范围/mm")
        self.lbl_zRange.setFont(self.fontNormal)
        self.lbl_xyInterval = QLabel("X/Y Interval 间隔/mm")
        self.lbl_xyInterval.setFont(self.fontNormal)
        self.lbl_zInterval = QLabel("Z Interval 间隔/mm")
        self.lbl_zInterval.setFont(self.fontNormal)

        self.inp_xRange = QLineEdit(scanningParameters['xRange'])
        self.inp_xRange.setFixedHeight(30)
        self.inp_xRange.setFont(self.fontNormal)
        self.inp_yRange = QLineEdit(scanningParameters['yRange'])
        self.inp_yRange.setFixedHeight(30)
        self.inp_yRange.setFont(self.fontNormal)
        self.inp_zRange = QLineEdit(scanningParameters['zRange'])
        self.inp_zRange.setFixedHeight(30)
        self.inp_zRange.setFont(self.fontNormal)
        self.inp_xyInterval = QLineEdit(scanningParameters['xyInterval'])
        self.inp_xyInterval.setFixedHeight(30)
        self.inp_xyInterval.setFont(self.fontNormal)
        self.inp_zInterval = QLineEdit(scanningParameters['zInterval'])
        self.inp_zInterval.setFixedHeight(30)
        self.inp_zInterval.setFont(self.fontNormal)

        self.btn_scanXY = QPushButton("Scan XY")
        self.btn_scanXY.clicked.connect(self.scanXY)
        self.btn_scanXY.setFixedHeight(50)
        self.btn_scanXY.setFont(self.fontNormal)
        self.btn_scanXZ = QPushButton("Scan XZ")
        self.btn_scanXZ.clicked.connect(self.scanXZ)
        self.btn_scanXZ.setFixedHeight(50)
        self.btn_scanXZ.setFont(self.fontNormal)
        self.btn_scanYZ = QPushButton("Scan YZ")
        self.btn_scanYZ.clicked.connect(self.scanYZ)
        self.btn_scanYZ.setFixedHeight(50)
        self.btn_scanYZ.setFont(self.fontNormal)
        self.btn_scanXYZ = QPushButton("Scan XYZ")
        self.btn_scanXYZ.clicked.connect(self.scanXYZ)
        self.btn_scanXYZ.setFixedHeight(50)
        self.btn_scanXYZ.setFont(self.fontNormal)
        self.btn_scanPauseResume = QPushButton("Pause/Resume")
        self.btn_scanPauseResume.clicked.connect(self.scanPauseResume)
        self.btn_scanPauseResume.setFixedHeight(50)
        self.btn_scanPauseResume.setFont(self.fontNormal)

        self.btn_saveWaveform = QPushButton("Save Waveform")
        self.btn_saveWaveform.clicked.connect(self.saveWaveform)
        self.btn_saveWaveform.setFixedHeight(50)
        self.btn_saveWaveform.setFont(self.fontNormal)

        # Log
        self.logTextBox = QTextEditLogger(self)
        logging.getLogger().addHandler(self.logTextBox)
        self.logTextBox.setFormatter(
            logging.Formatter('%(levelname)s - %(message)s'))  # ('%(asctime)s - %(levelname)s - %(message)s')
        self.logTextBox.setLevel(logging.getLevelName(logDetails['logLevelUI']))

        # Layouts
        # Define Layouts
        layout = QVBoxLayout()
        layout_general = QHBoxLayout()
        layout_position = QVBoxLayout()
        layout_positionRow1 = QHBoxLayout()
        layout_X = QHBoxLayout()
        layout_Y = QHBoxLayout()
        layout_Z = QHBoxLayout()
        layout_singleAxisMovement = QVBoxLayout()
        layout_multiAxisMovement = QHBoxLayout()
        gblayout_general = QGroupBox("General 通用设置")
        gblayout_position = QGroupBox("Position Settings 位置设置")
        gblayout_singleAxisMovement = QGroupBox("Single Axis Movement 单轴运动")
        gblayout_multiAxisMovement = QGroupBox("Multi Axis Movement 多轴运动")
        gblayout_oscilloscopeMeasurements = QGroupBox("Oscilloscope Measurements 示波器测量")
        gblayout_log = QGroupBox("Log Panel 日志面板")

        gblayout_general.setFont(self.fontHeader)
        gblayout_position.setFont(self.fontHeader)
        gblayout_singleAxisMovement.setFont(self.fontHeader)
        gblayout_multiAxisMovement.setFont(self.fontHeader)
        gblayout_oscilloscopeMeasurements.setFont(self.fontHeader)
        gblayout_log.setFont(self.fontHeader)

        # Layout General
        layout_general.addWidget(self.btn_start)
        layout_general.addStretch()
        layout_general.addWidget(self.btn_stop)
        layout_general.addStretch()
        layout_general.addWidget(self.btn_exit)

        # Layout Position
        layout_positionRow1.addWidget(self.btn_initialise)
        layout_positionRow1.addStretch()
        layout_positionRow1.addWidget(self.btn_saveFP)
        layout_positionRow1.addWidget(self.btn_moveFP)
        layout_positionRow1.addWidget(self.lbl_FP)
        layout_position.addLayout(layout_positionRow1)
        layout_position.addWidget(self.lbl_posRelFP)

        # Layout X Axis
        layout_X.addWidget(self.lbl_xPos)
        layout_X.addStretch()
        layout_X.addWidget(self.btn_moveXMinus1x)
        layout_X.addWidget(self.btn_moveXMinus01x)
        layout_X.addWidget(self.inp_moveX)
        layout_X.addWidget(self.btn_moveXPlus01x)
        layout_X.addWidget(self.btn_moveXPlus1x)
        layout_X.addStretch()
        layout_X.addWidget(self.btn_moveXMoveTo)
        # Layout Y Axis
        layout_Y.addWidget(self.lbl_yPos)
        layout_Y.addStretch()
        layout_Y.addWidget(self.btn_moveYMinus1x)
        layout_Y.addWidget(self.btn_moveYMinus01x)
        layout_Y.addWidget(self.inp_moveY)
        layout_Y.addWidget(self.btn_moveYPlus01x)
        layout_Y.addWidget(self.btn_moveYPlus1x)
        layout_Y.addStretch()
        layout_Y.addWidget(self.btn_moveYMoveTo)
        # Layout Z Axis
        layout_Z.addWidget(self.lbl_zPos)
        layout_Z.addStretch()
        layout_Z.addWidget(self.btn_moveZMinus1x)
        layout_Z.addWidget(self.btn_moveZMinus01x)
        layout_Z.addWidget(self.inp_moveZ)
        layout_Z.addWidget(self.btn_moveZPlus01x)
        layout_Z.addWidget(self.btn_moveZPlus1x)
        layout_Z.addStretch()
        layout_Z.addWidget(self.btn_moveZMoveTo)
        # Single Axis Movement
        layout_singleAxisMovement.addLayout(layout_X)
        layout_singleAxisMovement.addLayout(layout_Y)
        layout_singleAxisMovement.addLayout(layout_Z)

        # Layout XYZ Coordinates
        layout_multiAxisMovement.addWidget(self.inp_X)
        layout_multiAxisMovement.addWidget(self.inp_Y)
        layout_multiAxisMovement.addWidget(self.inp_Z)
        layout_multiAxisMovement.addStretch()
        layout_multiAxisMovement.addWidget(self.btn_moveToAbs)
        layout_multiAxisMovement.addWidget(self.btn_moveToRel)

        # Layout Oscilloscope Measurements
        layout_oscilloscopeMeasurements = QGridLayout()
        layout_oscilloscopeMeasurements.addWidget(self.lbl_xRange, 0, 0)
        layout_oscilloscopeMeasurements.addWidget(self.lbl_yRange, 0, 1)
        layout_oscilloscopeMeasurements.addWidget(self.lbl_zRange, 0, 2)
        layout_oscilloscopeMeasurements.addWidget(self.lbl_xyInterval, 0, 3)
        layout_oscilloscopeMeasurements.addWidget(self.lbl_zInterval, 0, 4)
        layout_oscilloscopeMeasurements.addWidget(self.inp_xRange, 1, 0)
        layout_oscilloscopeMeasurements.addWidget(self.inp_yRange, 1, 1)
        layout_oscilloscopeMeasurements.addWidget(self.inp_zRange, 1, 2)
        layout_oscilloscopeMeasurements.addWidget(self.inp_xyInterval, 1, 3)
        layout_oscilloscopeMeasurements.addWidget(self.inp_zInterval, 1, 4)
        layout_oscilloscopeMeasurements.addWidget(self.btn_scanXY, 2, 0, 1, 1)
        layout_oscilloscopeMeasurements.addWidget(self.btn_scanXZ, 2, 1, 1, 1)
        layout_oscilloscopeMeasurements.addWidget(self.btn_scanYZ, 2, 2, 1, 1)
        layout_oscilloscopeMeasurements.addWidget(self.btn_scanXYZ, 2, 3, 1, 1)
        layout_oscilloscopeMeasurements.addWidget(self.btn_saveWaveform, 2, 4, 1, 1)
        # layout_oscilloscopeMeasurements.addWidget(self.btn_scanPauseResume,3,3,1,1)

        # Layout Log
        layout_log = QVBoxLayout()
        layout_log.addWidget(self.logTextBox.widget)

        # Combine Layouts
        gblayout_general.setLayout(layout_general)
        gblayout_position.setLayout(layout_position)
        gblayout_singleAxisMovement.setLayout(layout_singleAxisMovement)
        gblayout_multiAxisMovement.setLayout(layout_multiAxisMovement)
        gblayout_oscilloscopeMeasurements.setLayout(layout_oscilloscopeMeasurements)
        gblayout_log.setLayout(layout_log)

        layout.addWidget(gblayout_general)
        layout.addWidget(gblayout_position)
        layout.addWidget(gblayout_singleAxisMovement)
        layout.addSpacing(10)
        layout.addWidget(gblayout_multiAxisMovement)
        layout.addSpacing(10)
        layout.addWidget(gblayout_oscilloscopeMeasurements)
        layout.addSpacing(10)
        layout.addWidget(gblayout_log)

        self.setLayout(layout)

    # Methods and Widget Functions
    def createFile(self, filepath, filename):
        # <filepath>/<filename>_<timeNow>
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
        dateNow = datetime.now().strftime(r"%Y%m%d")
        timeNow = datetime.now().strftime(r"_%I_%M_%S")
        if "dateNow" in filename:
            filename = filename.replace("dateNow", dateNow)
        fullFilename = os.path.join(filepath, (filename + timeNow))
        return fullFilename

    def start(self):
        # Check Galil Connection
        try:
            g1.GOpen(otherSettings['galilIP'] + ' -s ALL')
            logging.info("Galil Connected: " + g1.GInfo())
        except:
            # galilConnected = False
            logging.info("Unable to connect to Galil")
            return

        # DP with Saved Position 保存位置.txt
        file = open("Saved Position 保存位置.txt", 'r')
        self.xPosCount = file.readline()[0:-1]  # remove \n
        self.yPosCount = file.readline()[0:-1]
        self.zPosCount = file.readline()
        file.close()
        file.close()

        try:
            self.xPosSaved = float(self.xPosCount) / self.unitA
            self.yPosSaved = float(self.yPosCount) / self.unitB
            self.zPosSaved = float(self.zPosCount) / self.unitC
        except:
            logging.debug(self.xPosCount + ',' + self.yPosCount + ',' + self.zPosCount)
            logging.info("Please press Initialise 请按 '初始化' 按键")
        else:
            self.updatePosLbl()
            if (abs(self.xPos - self.xPosSaved) > 0.01 or abs(self.yPos - self.yPosSaved > 0.01) or abs(
                    self.zPos - self.zPosSaved > 0.01)):
                logging.debug(
                    "Saved Position: " + str(self.xPosSaved) + ', ' + str(self.yPosSaved) + ', ' + str(self.zPosSaved))
                logging.debug("RP Position: " + str(self.xPos) + ', ' + str(self.yPos) + ', ' + str(self.zPos))
                logging.info("Please press Initialise 请按 '初始化' 按键")
            else:
                c1("DPA=" + str(self.xPosCount) + ";DPB=" + str(self.yPosCount) + ";DPC=" + str(self.zPosCount))
        # Update lbl_FP
        file = open("Focus Point Position 焦点位置.txt", 'r')
        fpXCount = file.readline()
        fpYCount = file.readline()
        fpZCount = file.readline()
        file.close()
        self.fpXmm = round(float(fpXCount) / self.unitA, 2)
        self.fpYmm = round(float(fpYCount) / self.unitB, 2)
        self.fpZmm = round(float(fpZCount) / self.unitC, 2)

        FP = (self.fpXmm, self.fpYmm, self.fpZmm)
        self.lbl_FP.setText(str(FP))

        # Add thread: c_cmdList
        self.threadcmdList = QThread()
        self.workerCmdList = c_cmdList(True)
        self.workerCmdList.moveToThread(self.threadcmdList)
        self.threadcmdList.started.connect(self.workerCmdList.run)
        self.workerCmdList.updatePos.connect(self.updatePosLbl)
        self.workerCmdList.log.connect(self.updateLog)
        self.workerCmdList.initialiseEnd.connect(lambda: logging.info("Initialise complete 初始化完成"))
        self.workerCmdList.finished.connect(self.threadcmdList.quit)
        self.workerCmdList.finished.connect(self.workerCmdList.deleteLater)
        self.threadcmdList.finished.connect(self.threadcmdList.deleteLater)
        self.threadcmdList.finished.connect(lambda: self.btn_stop.setEnabled(False))
        self.threadcmdList.finished.connect(lambda: logging.info("cmdList thread closed"))
        self.threadcmdList.finished.connect(lambda: self.btn_start.setEnabled(True))
        self.threadcmdList.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        # Set galil variables: counts/mm, sp, ac,dc
        c1("unitA=" + str(self.unitA))
        c1("unitB=" + str(self.unitB))
        c1("unitC=" + str(self.unitC))
        c1("spN=" + linearStage["speedNormal"])
        c1("acN=" + linearStage["accelerationNormal"])
        c1("dcN=" + linearStage["deccelerationNormal"])
        c1("spI=" + linearStage["speedInitialise"])
        c1("acI=" + linearStage["accelerationInitialise"])
        c1("dcI=" + linearStage["deccelerationInitialise"])
        c1("spS=" + linearStage["speedScanning"])
        c1("acS=" + linearStage["accelerationScanning"])
        c1("dcS=" + linearStage["deccelerationScanning"])
        c1("SPA = @ABS[unitA*spN]; SPB = @ABS[unitB*spN]; SPC = @ABS[unitC*spN]")
        c1("ACA = @ABS[unitA*acN]; ACB = @ABS[unitB*acN]; ACC = @ABS[unitC*acN]")
        c1("DCA = @ABS[unitA*dcN]; DCB = @ABS[unitB*dcN]; DCC = @ABS[unitC*dcN]")

        # Disable start button, Enable all widgets
        self.enableWidgets(True)

    def stop(self):
        logging.warning("Stop Pressed")
        self.enableWidgets(False)
        cmdList.clear()
        c1("ST")
        logging.debug("Galil: ST")
        self.end()

    def end(self):
        # write in txt file
        file = open("Saved Position 保存位置.txt", 'w+')
        try:
            file.write('\n'.join([c1("RPA"), c1("RPB"), c1("RPC")]))
        except:
            pass
        file.close()
        # #close threads
        try:
            self.workerCmdList.activeCmdList = False
        except:
            pass
        try:
            self.workerScanXYZ.activeScanXYZ = False
        except:
            pass

    def exit(self):
        self.btn_exit.setEnabled(False)
        # wait for all commands to finish
        while len(cmdList) > 0:
            pass
        self.end()
        self.close()

    def initialise(self):
        # Move to origin, set as (0,0,0), move to midpoint
        midptA = linearStage['midptA']
        midptB = linearStage['midptB']
        midptC = linearStage['midptC']
        if (self.XLimMin > 0 and self.unitA > 0):  # out of range when initialise
            c1("flipA = 1")  # tell galil to initialise in opposite direction
            c1("initptA = " + str(self.XLimMax))
        else:
            c1("flipA = 0")
            c1("initptA = " + str(self.XLimMin))
        if (self.YLimMin > 0 and self.unitB > 0):
            c1("flipB = 1")
            c1("initptB = " + str(self.YLimMax))
        else:
            c1("flipB = 0")
            c1("initptB = " + str(self.YLimMin))
        if (self.ZLimMin > 0 and self.unitC > 0):
            c1("flipC = = 1")
            c1("initptC = " + str(self.ZLimMax))
        else:
            c1("flipC = 0")
            c1("initptC = " + str(self.ZLimMin))
        cmdList.append("midptA=" + midptA + ";midptB=" + midptB + ";midptC=" + midptC)
        cmdList.append("XQ #midpt, 3")
        logging.info("Initialise start 初始化开始")

    def saveFP(self):
        # Save in txt file
        fpXCount = c1("RPA")
        fpYCount = c1("RPB")
        fpZCount = c1("RPC")
        file = open("Focus Point Position 焦点位置.txt", 'w+')
        file.write('\n'.join([fpXCount, fpYCount, fpZCount]))
        file.close()

        # Update lbl_FP
        self.fpXmm = round(float(fpXCount) / self.unitA, 2)
        self.fpYmm = round(float(fpYCount) / self.unitB, 2)
        self.fpZmm = round(float(fpZCount) / self.unitC, 2)

        FP = (self.fpXmm, self.fpYmm, self.fpZmm)
        self.lbl_FP.setText(str(FP))

    def moveFP(self):
        # move to FP
        file = open("Focus Point Position 焦点位置.txt", 'r')
        fpXCount = file.readline().strip()
        fpYCount = file.readline().strip()
        fpZCount = file.readline().strip()
        file.close()

        cmdList.append("PAA=" + fpXCount + ";PAB=" + fpYCount + ";PAC=" + fpZCount + ";SHABC;BGABC")

        # Update lbl_FP
        self.fpXmm = round(float(fpXCount) / self.unitA, 2)
        self.fpYmm = round(float(fpYCount) / self.unitB, 2)
        self.fpZmm = round(float(fpZCount) / self.unitC, 2)

        FP = (self.fpXmm, self.fpYmm, self.fpZmm)
        self.lbl_FP.setText(str(FP))

    def moveX(self, moveMultiply):
        try:
            input = float(self.inp_moveX.text())
            move_mm = input * moveMultiply
            if ((self.xPos + move_mm) >= self.XLimMin) and ((self.xPos + move_mm) <= self.XLimMax):
                steps = round(self.unitA * move_mm, 5)
                cmdList.append("PRA=" + str(steps) + ";SHA;BGA")
            else:
                logging.error("out of range (X axis)")
        except ValueError:
            logging.error("input is not a number")

    def moveY(self, moveMultiply):
        try:
            input = float(self.inp_moveY.text())
            move_mm = input * moveMultiply
            if ((self.yPos + move_mm) >= self.YLimMin) and ((self.yPos + move_mm) <= self.YLimMax):
                steps = round(self.unitB * move_mm, 5)
                cmdList.append("PRB=" + str(steps) + ";SHB;BGB")
            else:
                logging.error("out of range (Y axis)")
        except ValueError:
            logging.error("input is not a number")

    def moveZ(self, moveMultiply):
        try:
            input = float(self.inp_moveZ.text())
            move_mm = input * moveMultiply
            if ((self.zPos + move_mm) >= self.ZLimMin) and ((self.zPos + move_mm) <= self.ZLimMax):
                steps = round(self.unitC * move_mm, 5)
                cmdList.append("PRC=" + str(steps) + ";SHC;BGC")
            else:
                logging.error("out of range (Z axis)")
        except ValueError:
            logging.error("input is not a number")

    def moveXMoveTo(self):
        try:
            input = float(self.inp_moveX.text())
            if (input >= self.XLimMin) and (input <= self.XLimMax):
                move_to_counts = input * self.unitA
                cmdList.append("PAA=" + str(move_to_counts) + ";SHA;BGA")
            else:
                logging.error("out of range (X axis)")
        except ValueError:
            logging.error("input is not a number")

    def moveYMoveTo(self):
        try:
            input = float(self.inp_moveY.text())
            if (input >= self.YLimMin) and (input <= self.YLimMax):
                move_to_counts = input * self.unitB
                cmdList.append("PAB=" + str(move_to_counts) + ";SHB;BGB")
            else:
                logging.error("out of range (Y axis)")
        except ValueError:
            logging.error("input is not a number")

    def moveZMoveTo(self):
        try:
            input = float(self.inp_moveZ.text())
            if (input >= self.ZLimMin) and (input <= self.ZLimMax):
                move_to_counts = input * self.unitC
                cmdList.append("PAC=" + str(move_to_counts) + ";SHC;BGC")
            else:
                logging.error("out of range (Z axis)")
        except ValueError:
            logging.error("input is not a number")

    def updatePosLbl(self):
        # XYZ Absolute Positions
        try:
            self.xPosCount = c1("RPA")
            self.yPosCount = c1("RPB")
            self.zPosCount = c1("RPC")
        except:
            time.sleep(0.01)
            self.xPosCount = c1("RPA")
            self.yPosCount = c1("RPB")
            self.zPosCount = c1("RPC")
        self.xPos = float(self.xPosCount) / self.unitA
        self.yPos = float(self.yPosCount) / self.unitB
        self.zPos = float(self.zPosCount) / self.unitC

        self.xPosRound = round(self.xPos, 2)
        self.yPosRound = round(self.yPos, 2)
        self.zPosRound = round(self.zPos, 2)

        self.lbl_xPos.setText("Position 位置: " + str(self.xPosRound) + "mm")
        self.lbl_yPos.setText("Position 位置: " + str(self.yPosRound) + "mm")
        self.lbl_zPos.setText("Position 位置: " + str(self.zPosRound) + "mm")

        # XYZ Relative Positions to FP
        try:
            self.XposRelFP = round(self.xPos - self.fpXmm, 2)
            self.YposRelFP = round(self.yPos - self.fpYmm, 2)
            self.ZposRelFP = round(self.zPos - self.fpZmm, 2)

            self.lbl_posRelFP.setText("Position Relative to FP 焦点相对位置/mm: (" + str(self.XposRelFP) + " , " + str(
                self.YposRelFP) + " , " + str(self.ZposRelFP) + ")")
        except:
            pass

    def updateLog(self, inputText, logLevel):  # logging for threads
        if logLevel == 'debug':
            logging.debug(inputText)
        elif logLevel == 'info':
            logging.info(inputText)
        elif logLevel == 'warning':
            logging.warning(inputText)
        elif logLevel == 'error':
            logging.error(inputText)

    def moveToAbs(self):
        try:
            inputX = float(self.inp_X.text())
            inputY = float(self.inp_Y.text())
            inputZ = float(self.inp_Z.text())
        except ValueError:
            logging.error("input is not a number")
        else:
            move_to_counts_X = inputX * self.unitA
            move_to_counts_Y = inputY * self.unitB
            move_to_counts_Z = inputZ * self.unitC
            cmdList.append("PAA=" + str(move_to_counts_X) + ";PAB=" + str(move_to_counts_Y) + ";PAC=" + str(
                move_to_counts_Z) + ";SHABC;BGABC")

    def moveToRel(self):
        try:
            inputX = float(self.inp_X.text())
            inputY = float(self.inp_Y.text())
            inputZ = float(self.inp_Z.text())
        except ValueError:
            logging.error("input is not a number")
        else:
            move_to_counts_X = inputX * self.unitA
            move_to_counts_Y = inputY * self.unitB
            move_to_counts_Z = inputZ * self.unitC
            cmdList.append("PRA=" + str(move_to_counts_X) + ";PRB=" + str(move_to_counts_Y) + ";PRC=" + str(
                move_to_counts_Z) + ";SHABC;BGABC")

    def connectOscilloscope(self):
        self.rm = visa.ResourceManager()
        try:
            visaResourceAddr = otherSettings['oscilloscopeID']
            self.scope = self.rm.open_resource(visaResourceAddr)
            self.scope.timeout = 5000
            logging.info("Connected to oscilloscope: " + self.scope.query("*idn?")[0:-1])
            connectError = 0
        except:
            logging.error("Error connecting to oscilloscope: " + sys.exc_info()[1].args[0])
            connectError = 1
        return (connectError)

    def plot(self, xAxis, yAxis, saveLocationPlot):
        plt.plot(xAxis, yAxis)
        plt.title('CH1 Waveform')  # plot label
        plt.xlabel('Time (s)')  # x label
        plt.ylabel('Voltage (V)')  # y label
        plt.show()
        plt.savefig(saveLocationPlot + '.png')

    def saveWaveform(self):
        self.connectOscilloscope()
        # Add thread: saveWaveform
        self.threadSaveWaveform = QThread()
        self.workerSaveWaveform = c_saveWaveform()
        self.workerSaveWaveform.moveToThread(self.threadSaveWaveform)
        self.threadSaveWaveform.started.connect(self.workerSaveWaveform.saveWaveform)
        self.workerSaveWaveform.log.connect(self.updateLog)
        self.workerSaveWaveform.plot.connect(self.plot)
        self.workerSaveWaveform.finished.connect(self.threadSaveWaveform.quit)
        self.workerSaveWaveform.finished.connect(self.workerSaveWaveform.deleteLater)
        self.threadSaveWaveform.finished.connect(self.threadSaveWaveform.deleteLater)
        self.threadSaveWaveform.finished.connect(lambda: self.btn_saveWaveform.setEnabled(True))
        self.threadSaveWaveform.finished.connect(lambda: self.scope.close())
        self.threadSaveWaveform.finished.connect(lambda: self.rm.close())
        self.threadSaveWaveform.start()
        self.btn_saveWaveform.setEnabled(False)

        # plot
        # plt.plot(scaledTime, scaledVolt)
        # plt.title('CH1 Waveform') # plot label
        # plt.xlabel('Time (s)') # x label
        # plt.ylabel('Voltage (V)') # y label
        # plt.show()
        # plt.savefig(fullFilename + '.png')

    def scanCheck(self):
        autorunError = 0
        # check that there is a FP recorded
        try:
            if self.fpXmm == 0 and self.fpYmm == 0 and self.fpZmm == 0:
                autorunError = 1
                logging.error("No focus point recorded")
        except:
            logging.error("Press start")
            return
        # check that motion is within range
        try:
            self.xRange_float = float(self.inp_xRange.text())
            self.yRange_float = float(self.inp_yRange.text())
            self.zRange_float = float(self.inp_zRange.text())
            self.XYInterval = float(self.inp_xyInterval.text())
            self.ZInterval = float(self.inp_zInterval.text())
        except ValueError:
            autorunError = 1
            logging.error("range/interval input is not a number")
        else:
            self.XStart = round(self.fpXmm - self.xRange_float / 2, 2)
            self.XEnd = round(self.fpXmm + self.xRange_float / 2, 2)
            self.YStart = round(self.fpYmm - self.yRange_float / 2, 2)
            self.YEnd = round(self.fpYmm + self.yRange_float / 2, 2)
            self.ZStart = round(self.fpZmm - self.zRange_float / 2, 2)
            self.ZEnd = round(self.fpZmm + self.zRange_float / 2, 2)
            if (self.XStart / 2) <= self.XLimMin or (self.XEnd / 2) >= self.XLimMax:
                autorunError = 1
                logging.error("out of range (X axis)")
            if (self.YStart / 2) <= self.YLimMin or (self.YEnd / 2) >= self.YLimMax:
                autorunError = 1
                logging.error("out of range (Y axis)")
            if (self.ZStart / 2) <= self.ZLimMin or (self.ZEnd / 2) >= self.ZLimMax:
                autorunError = 1
                logging.error("out of range (Z axis)")
        # connect to oscilloscope
        autorunError = self.connectOscilloscope()
        return (autorunError)

    def scanGetLocations(self, start, end, fp, interval):
        # make sure number of points is an integer
        startUpdated = fp
        while startUpdated > start:
            startUpdated = round(startUpdated - interval, 2)
        endUpdated = fp
        while endUpdated < end:
            endUpdated = round(endUpdated + interval, 2)
        rangeUpdated = round(endUpdated - startUpdated, 2)
        numPoints = int(rangeUpdated / interval + 1)  # number of points
        locations = np.linspace(startUpdated, endUpdated, numPoints)
        return (rangeUpdated, locations)

    def addScanThread(self, axis, fullFilename, locationsAxis0, locationsAxis1, locationsAxis2):
        # Add thread: scanXYZ
        self.threadScanXYZ = QThread()
        self.workerScanXYZ = c_scanXYZ(True, fullFilename, axis, locationsAxis0, locationsAxis1, locationsAxis2)
        # c_scanXYZ inputs: (activeScanXYZ, fullFilename, axis, locationsAxis0, locationsAxis1, locationsAxis2) #axis=[axis0,axis1,axis2]
        self.workerScanXYZ.moveToThread(self.threadScanXYZ)
        self.threadScanXYZ.started.connect(self.workerScanXYZ.recordData)
        self.workerScanXYZ.log.connect(self.updateLog)
        self.workerScanXYZ.finished.connect(self.threadScanXYZ.quit)
        self.workerScanXYZ.finished.connect(self.workerScanXYZ.deleteLater)
        self.threadScanXYZ.finished.connect(self.threadScanXYZ.deleteLater)
        self.threadScanXYZ.finished.connect(lambda: self.btn_scanXY.setEnabled(True))
        self.threadScanXYZ.finished.connect(lambda: self.btn_scanXZ.setEnabled(True))
        self.threadScanXYZ.finished.connect(lambda: self.btn_scanYZ.setEnabled(True))
        self.threadScanXYZ.finished.connect(lambda: self.btn_scanXYZ.setEnabled(True))
        self.threadScanXYZ.finished.connect(lambda: logging.info("Scan thread closed"))
        self.threadScanXYZ.finished.connect(lambda: self.scope.close())
        self.threadScanXYZ.finished.connect(lambda: self.rm.close())
        self.threadScanXYZ.start()
        self.scanStart = datetime.now()
        self.btn_scanXY.setEnabled(False)
        self.btn_scanXZ.setEnabled(False)
        self.btn_scanYZ.setEnabled(False)
        self.btn_scanXYZ.setEnabled(False)

    def scanXY(self):
        autorunError = self.scanCheck()
        # START HERE
        if autorunError == 0:
            # come up with location points
            #   (rangeUpdated,locations)=scanGetLocations(self,start,end,fp,interval)
            (xRangeUpdated, locationsX) = self.scanGetLocations(self.XStart, self.XEnd, self.fpXmm, self.XYInterval)
            if (self.xRange_float - xRangeUpdated) > 0.01:
                self.xRange_float = xRangeUpdated
                self.inp_xRange.setText(str(self.xRange_float))
                logging.info("X Range changed to " + str(self.xRange_float))
            (yRangeUpdated, locationsY) = self.scanGetLocations(self.YStart, self.YEnd, self.fpYmm, self.XYInterval)
            if (self.yRange_float - yRangeUpdated) > 0.01:
                self.yRange_float = yRangeUpdated
                self.inp_yRange.setText(str(self.yRange_float))
                logging.info("Y Range changed to " + str(self.yRange_float))
            locationsZ = [self.fpZmm]
            # pass data to start scan thread
            fullFilename = self.createFile(otherSettings['saveLocationData'], "水听器测试_dateNow_XY")
            self.addScanThread(['x', 'y', 'z'], fullFilename, locationsX, locationsY, locationsZ)
            # addScanThread inputs: (axis,locationsAxis0, locationsAxis1, locationsAxis2)
        else:
            logging.info("Did not run program")

    def scanXZ(self):
        autorunError = self.scanCheck()
        # START HERE
        if autorunError == 0:
            # come up with location points
            #   (rangeUpdated,locations)=scanGetLocations(self,start,end,fp,interval)
            (xRangeUpdated, locationsX) = self.scanGetLocations(self.XStart, self.XEnd, self.fpXmm, self.XYInterval)
            if abs(self.xRange_float - xRangeUpdated) > 0.01:
                self.xRange_float = xRangeUpdated
                self.inp_xRange.setText(str(self.xRange_float))
                logging.info("X Range changed to " + str(self.xRange_float))
            (zRangeUpdated, locationsZ) = self.scanGetLocations(self.ZStart, self.ZEnd, self.fpZmm, self.ZInterval)
            if abs(self.zRange_float - zRangeUpdated) > 0.01:
                self.zRange_float = zRangeUpdated
                self.inp_zRange.setText(str(self.zRange_float))
                logging.info("Z Range changed to " + str(self.zRange_float))
            locationsY = [self.fpYmm]
            fullFilename = self.createFile(otherSettings['saveLocationData'], "水听器测试_dateNow_XZ")
            self.addScanThread(['x', 'z', 'y'], fullFilename, locationsX, locationsZ, locationsY)
            # addScanThread inputs: (axis,fullFilename, locationsAxis0, locationsAxis1, locationsAxis2)
        else:
            logging.info("Did not run program")

    def scanYZ(self):
        autorunError = self.scanCheck()
        # START HERE
        if autorunError == 0:
            # come up with location points
            #   (rangeUpdated,locations)=scanGetLocations(self,start,end,fp,interval)
            (yRangeUpdated, locationsY) = self.scanGetLocations(self.YStart, self.YEnd, self.fpYmm, self.XYInterval)
            if abs(self.yRange_float - yRangeUpdated) > 0.01:
                self.yRange_float = yRangeUpdated
                self.inp_yRange.setText(str(self.yRange_float))
                logging.info("Y Range changed to " + str(self.yRange_float))
            (zRangeUpdated, locationsZ) = self.scanGetLocations(self.ZStart, self.ZEnd, self.fpZmm, self.ZInterval)
            if abs(self.zRange_float - zRangeUpdated) > 0.01:
                self.zRange_float = zRangeUpdated
                self.inp_zRange.setText(str(self.zRange_float))
                logging.info("Z Range changed to " + str(self.zRange_float))
            locationsX = [self.fpXmm]
            fullFilename = self.createFile(otherSettings['saveLocationData'], "水听器测试_dateNow_YZ")
            self.addScanThread(['y', 'z', 'x'], fullFilename, locationsY, locationsZ, locationsX)
            # addScanThread inputs: (axis,locationsAxis0, locationsAxis1, locationsAxis2)
        else:
            logging.info("Did not run program")

    def scanXYZ(self):
        autorunError = self.scanCheck()
        # START HERE
        if autorunError == 0:
            # come up with location points
            #   (rangeUpdated,locations)=scanGetLocations(self,start,end,fp,interval)
            (xRangeUpdated, locationsX) = self.scanGetLocations(self.XStart, self.XEnd, self.fpXmm, self.XYInterval)
            if abs(self.xRange_float - xRangeUpdated) > 0.01:
                self.xRange_float = xRangeUpdated
                self.inp_xRange.setText(str(self.xRange_float))
                logging.info("X Range changed to " + str(self.xRange_float))
            (yRangeUpdated, locationsY) = self.scanGetLocations(self.YStart, self.YEnd, self.fpYmm, self.XYInterval)
            if abs(self.yRange_float - yRangeUpdated) > 0.01:
                self.yRange_float = yRangeUpdated
                self.inp_yRange.setText(str(self.yRange_float))
                logging.info("Y Range changed to " + str(self.yRange_float))
            (zRangeUpdated, locationsZ) = self.scanGetLocations(self.ZStart, self.ZEnd, self.fpZmm, self.ZInterval)
            if abs(self.zRange_float - zRangeUpdated) > 0.01:
                self.zRange_float = zRangeUpdated
                self.inp_zRange.setText(str(self.zRange_float))
                logging.info("Z Range changed to " + str(self.zRange_float))
            fullFilename = self.createFile(otherSettings['saveLocationData'], "水听器测试_dateNow_XYZ")
            self.addScanThread(['x', 'y', 'z'], fullFilename, locationsX, locationsY, locationsZ)
            # addScanThread inputs: (axis,locationsAxis0, locationsAxis1, locationsAxis2)
        else:
            logging.info("Did not run program")

    def scanPauseResume(self):
        pass


if __name__ == '__main__':
    # Read config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    otherSettings = config['otherSettings']
    linearStage = config['linearStage']
    logDetails = config['logDetails']
    scanningParameters = config['scanningParameters']

    # start logging
    saveLocationLog = otherSettings['saveLocationLog']
    if not os.path.isdir(saveLocationLog):
        os.makedirs(saveLocationLog)
    timeNow = datetime.now().strftime(r"_%Y%m%d_%I_%M_%S")
    fullFilename = os.path.join(saveLocationLog, (timeNow + ".txt"))
    logLevelFile = logDetails['logLevelFile']
    logging.basicConfig(filename=fullFilename, level=logging.getLevelName(logLevelFile),
                        format='%(asctime)s:%(levelname)s:%(message)s')

    # If no txt file, create
    if os.path.isfile("Saved Position 保存位置.txt") == False:
        file = open("Saved Position 保存位置.txt", 'w+')
        file.write('\n'.join(['0', '0', '0']))
        file.close()

    if os.path.isfile("Focus Point Position 焦点位置.txt") == False:
        file = open("Focus Point Position 焦点位置.txt", 'w+')
        file.write('\n'.join(['0', '0', '0']))
        file.close()

    # Setup gclib
    g1 = gclib.py()
    c1 = g1.GCommand  # alias the command callable

    # Open UI
    app = QApplication(sys.argv)
    window = Display()
    window.windowLocation()
    window.show()
    window.raise_()
    app.exec_()
    sys.exit(app.exec_())
