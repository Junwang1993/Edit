import csv
import DataPreprocessing
from collections import defaultdict
import Time
from io import open
import numpy as np

class CsvReader(object):
    def __init__(self, file):
        self.fileName = file

    def getData(self, indexs, hasHeader, needHandleNegativeOneIndex, flag):
        data = []
        columns = defaultdict(list)  # each value in each column is appended to a list

        with open(self.fileName, encoding='Latin-1') as f:
            reader = csv.reader(f, delimiter = ",",quoting=csv.QUOTE_NONE)  # read rows into a dictionary format
            if hasHeader == 1:
                next(reader)
                next(reader)
            for row in reader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)
        for j in indexs:
            newColumns = columns[j]
            if j in needHandleNegativeOneIndex:

                newColumns = DataPreprocessing.DataPreprocessing().handleNegativeOneV2([float(i) for i in newColumns], flag = False)
            data.append(newColumns)
        # minLength
        allLengths = []
        for i in range(0, len(data)):
            allLengths.append(len(data[i]))
        minLength = np.array(allLengths).min()
        for i in range(0, len(data)):
            data[i] = data[i][0:minLength]
        return data

    def getBlink1D(self):
        # some variables
        hasHeader = 1

        return1D = []
        columns = defaultdict(list)
        with open(self.fileName) as f:
            reader = csv.reader(f, delimiter = ",")  # read rows into a dictionary format
            if hasHeader == 1:
                next(reader)
                next(reader)
            for row in reader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)
        dataValue = columns[2]
        at = columns[0]
        return1D = CsvReader.convertRawGazeDataToBlink(at, dataValue)
        return return1D

    @staticmethod
    def convertRawGazeDataToBlink(at, data):
        return1D = []
        # some global variables
        bd = 400.0
        f = 60.0
        maxNum = int(bd / (1000.0 / f) + 0.5)
        bd = 100.0
        minNum = int(bd / (1000.0 / f) + 0.5)
        # -1 chunk
        pointer_front = 0
        pointer_back = 0
        while pointer_front < len(data):
            check = data[pointer_front]
            if float(data[pointer_front]) != -1.0:
                pointer_front += 1
            else:
                # enter -1 area
                pointer_back = pointer_front+1
                while pointer_back < len(data):
                    if float(data[pointer_back]) != -1.0:
                        break
                    else:
                        pointer_back +=1
                if pointer_back-pointer_front <= maxNum and pointer_back-pointer_front>= minNum:
                    return1D.append(at[pointer_front])
                    return1D.append(at[pointer_back-1])
                pointer_front = pointer_back
        return1D = [Time.Time(i) for i in return1D]
        return  return1D


