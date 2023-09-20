#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
"""
This class creates an instance of the Trigno base. Put in your key and license here
"""
import clr
import numpy as np
from collections import deque

clr.AddReference("devices/hardware/delsys/delsys/delsysAPI/resources/DelsysAPI")
clr.AddReference("System.Collections")

from Aero import AeroPy  # type: ignore # noqa: E402
from System.Collections.Generic import List  # type: ignore # noqa: E402
from System import Int32  # type: ignore # noqa: E402


class Delsys():

    def __init__(self):

        self.key = ""

        self.license = ""

        self.TrigBase = AeroPy()

        self.packetCount = 0
        self.sampleCount = 0
        self.EMGBuffer = 0
        self.emg_plot = deque()
        self.isSetupDone = False
        self.isInDebugMode = False
        self.basisForDebugging = np.ones((8, 3))
        self.realDataStreamID = 0

    def connect(self) -> None:
        """
        Connect to the base
        """
        self.TrigBase.ValidateBase(self.key, self.license, "RF")

    def pair(self) -> None:
        """
        Enter pair mode for new sensors
        """
        self.TrigBase.PairSensors()

    def scan(self) -> None:
        """
        Scan for any available sensors
        """
        self.TrigBase.ScanSensors().Result
        self.nameList = self.TrigBase.ListSensorNames()
        self.SensorsFound = len(self.nameList)

        self.TrigBase.ConnectSensors()
        self.isSetupDone = True

    def start(self) -> None:
        """
        Start the data stream from Sensors
        """
        newTransform = self.TrigBase.CreateTransform("raw")
        index = List[Int32]()

        self.TrigBase.ClearSensorList()

        for i in range(self.SensorsFound):
            selectedSensor = self.TrigBase.GetSensorObject(i)
            self.TrigBase.AddSensortoList(selectedSensor)
            index.Add(i)

        self.sampleRates = [[] for i in range(self.SensorsFound)]
        self.TrigBase.StreamData(index, newTransform, 1)

        self.dataStreamIdx = []
        # self.plotCount = 0
        idxVal = 0
        for i in range(self.SensorsFound):
            selectedSensor = self.TrigBase.GetSensorObject(i)
            for channel in range(len(selectedSensor.TrignoChannels)):
                self.sampleRates[i].append((selectedSensor.TrignoChannels[channel].SampleRate, selectedSensor.TrignoChannels[channel].Name))
                if "EMG" in selectedSensor.TrignoChannels[channel].Name:
                    self.dataStreamIdx.append(idxVal)
                    # self.plotCount+=1
                idxVal += 1

    def stop(self) -> None:
        """
        Stop the data stream
        """
        self.TrigBase.StopData()

    # Helper Functions
    def getSampleModes(self, sensorIdx):
        """
        Gets the list of sample modes available for selected sensor
        """
        sampleModes = self.TrigBase.ListSensorModes(sensorIdx)
        return sampleModes

    def getCurMode(self):
        """
        Gets the current mode of the sensors
        """
        curMode = self.TrigBase.GetSampleMode()
        return curMode

    def setSampleMode(self, curSensor, setMode):
        """
        Sets the sample mode for the selected sensor
        """
        self.TrigBase.SetSampleMode(curSensor, setMode)

    def getEMGData(self):

        outArr = self.GetData()
        if outArr is not None:
            outData = list(np.asarray(outArr)[tuple([self.dataStreamIdx])])
            new = np.asarray(outData)
            self.EMGBuffer = new
            return self.EMGBuffer
        else:
            return None

    def GetData(self):
        """
        Callback to get the data from the streaming sensors
        """
        dataReady = self.TrigBase.CheckDataQueue()
        if dataReady:
            DataOut = self.TrigBase.PollData()
            if len(DataOut) > 0:  # Check for lost Packets, len(DataOut) = #Channels(8) * #Sensor(EMG+ACC_X_Y_Z = 4) = 32
                outArr = [[] for i in range(len(DataOut))]
                for j in range(len(DataOut)):
                    if len(DataOut[j]) > 1:
                        print('Packet accumulation!!!')
                    for k in range(len(DataOut[j])):
                        outBuf = DataOut[j][k]
                        outArr[j].extend(outBuf)
                return outArr
            else:
                return None
        else:
            return None

# region Helpers
    def getPacketCount(self):
        return self.packetCount

    def resetPacketCount(self):
        self.packetCount = 0
        self.sampleCount = 0

    def getSampleCount(self):
        return self.sampleCount
