import copy
import Time
import numpy as np
import sys
from pandas import Series

class DataPreprocessing(object):
    @staticmethod
    def movingaverage(y, N):
        y_padded = np.pad(y, (N // 2, N - 1 - N // 2), mode='edge')
        y_smooth = np.convolve(y_padded, np.ones((N,)) / N, mode='valid')
        return y_smooth

    @staticmethod
    def reject_outliers(sr, iq_range=0.5):
        pcnt = (1 - iq_range) / 2
        qlow, median, qhigh = sr.dropna().quantile([pcnt, 0.50, 1 - pcnt])
        iqr = qhigh - qlow
        return sr[(sr - median).abs() <= iqr]
    @staticmethod
    def findAdjustAtTime(gaze_at_list, EDA_at_list):
        WALKDIFF = 5000  #
        # diff measures the ***gaze - EDA***
        at_gaze_last = gaze_at_list[-1]
        at_eda_last = EDA_at_list[-1]
        diff = Time.Time().substractionBetweenTwoTime(at_eda_last, at_gaze_last)

        return diff + WALKDIFF  # this diff need to add to eda

    @staticmethod
    def adjustEDAAtList(EDA_at_list, diffGME):
        returnAtList = []
        for at in EDA_at_list:
            if diffGME >= 0:
                t = Time.Time().addByNms(at, diffGME)
            else:
                t = Time.Time().substractByNms(at, abs(diffGME))
            returnAtList.append(t)
        return returnAtList

    @staticmethod
    def interpolateMappingB2A(A, B):
        # input format A = [at, location] B = [at, location]
        at_A = A[0]
        at_B = B[0]
        A_correspondingToB = []
        for i in range(0, len(A)):
            A_correspondingToB.append([])
        B_converted = []
        for i in range(0, len(B)):
            B_converted.append([])
        j = 0
        for i in range(0, len(at_A)):
            j+=1
            print(str(j))
            indexInB = Time.Time().findPositionInTimeArray(at_A[i], at_B)-1
            if indexInB <0 or indexInB+1>=len(at_B):
                continue
            else:
                fIndex_B = indexInB
                bIndex_B = indexInB+1
                # compute ratio
                totalTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B], at_B[bIndex_B])
                diffTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B], at_A[i])
                ratio = diffTimeIntervel / totalTimeIntervel
                #
                flocation_B = B[1][fIndex_B]
                blocation_B = B[1][bIndex_B]
                x = (blocation_B[0] - flocation_B[0])*ratio + flocation_B[0]
                y = (blocation_B[1] - flocation_B[1])*ratio + flocation_B[1]
                B_converted[0].append(at_A[i])
                B_converted[1].append((x, y))
                # refine A
                A_correspondingToB[0].append(at_A[i])
                A_correspondingToB[1].append(A[1][i])
        return A_correspondingToB, B_converted

    @staticmethod
    def interpolateMappingB2A3D(A, B):
        at_A = A[0]
        at_B = B[0]
        A_correspondingToB = []
        for i in range(0, len(A)):
            A_correspondingToB.append([])
        B_converted = []
        for i in range(0, len(B)):
            B_converted.append([])
        j = 0
        for i in range(0, len(at_A)):
            j += 1
            print(str(j))
            indexInB = Time.Time().findPositionInTimeArray(at_A[i], at_B) - 1
            if indexInB < 0 or indexInB + 1 >= len(at_B):
                continue
            else:
                fIndex_B = indexInB
                bIndex_B = indexInB + 1
                # compute ratio
                totalTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B], at_B[bIndex_B])
                diffTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B], at_A[i])
                if totalTimeIntervel == 0:
                    totalTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B-1], at_B[bIndex_B])
                    diffTimeIntervel = Time.Time().substractionBetweenTwoTime(at_B[fIndex_B-1], at_A[i])
                ratio = diffTimeIntervel / totalTimeIntervel
                flocation_B = B[1][fIndex_B]
                blocation_B = B[1][bIndex_B]
                x = (blocation_B[0] - flocation_B[0]) * ratio + flocation_B[0]
                y = (blocation_B[1] - flocation_B[1]) * ratio + flocation_B[1]
                z = (blocation_B[2] - flocation_B[2]) * ratio + flocation_B[2]
                B_converted[0].append(at_A[i])
                B_converted[1].append((x, y, z))
                # refine A
                A_correspondingToB[0].append(at_A[i])
                A_correspondingToB[1].append(A[1][i])
        return A_correspondingToB, B_converted

    @staticmethod
    def fromMouseKeyboardDataFetchMouseData(data_KM):
        data_mouse = [[], []] # at, flag, (x, y)
        at_string = data_KM[0]
        flag = data_KM[1]
        X = data_KM[2]
        Y = data_KM[3]
        for i in range(0, len(at_string)):
            if flag[i] == 'MouseMoving':
                data_mouse[0].append(at_string[i])
                data_mouse[1].append((X[i],Y[i]))
        return data_mouse

    @staticmethod
    def generateClickInterval(dir, at_mouse, event_mouse):
        at_intervals = []
        indexClick = []
        for i in range(0, len(event_mouse)):
            if event_mouse[i] == 'MouseClicking':
                indexClick.append(i)
        # adding first chunk
        at_intervals.append((at_mouse[0], at_mouse[indexClick[0]]))
        for i in range(1, len(indexClick)):
            at_intervals.append((at_mouse[indexClick[i - 1]], at_mouse[indexClick[i]]))
        # adding last chunk
        at_intervals.append((at_mouse[indexClick[len(indexClick) - 1]], at_mouse[-1]))
        # write
        f = open(dir+'clickInterval.csv', 'w')
        for interval in at_intervals:
            f.write(interval[0])
            f.write(',')
            f.write(interval[1])
            f.write('\n')
        f.close()
        return at_intervals

    @staticmethod
    def hf1(values):
        values_c = []
        x2 = values.pop(0)
        x1 = values.pop(0)
        x = -1
        while len(values)>0:
            x = values.pop(0)
            if x2>x1 and x1<x:
                d1 = abs(x - x1)
                d2 = abs(x2 - x)
                if d1 < d2:
                    x1 = x
                else:
                    x1 =x2
            else:
                if x2<x1 and x1>x:
                    d1 = abs(x - x1)
                    d2 = abs(x2 - x1)
                    if d1 < d2:
                        x1 = x
                    else:
                        x1 = x2
            values_c.append(x2)
            x2 = x1
            x1 = x
        values_c.append(x2)
        values_c.append(x1)
        return values_c

    @staticmethod
    def hf2(values):
        values_c = []
        x3 = values.pop(0)
        x2 = values.pop(0)
        x1 = values.pop(0)
        x = -1
        while len(values)>0:
            x = values.pop(0)
            if x2 == x1:
                if x != x1:
                    if x2 != x3:
                        d1 = abs(x - x1)
                        d2 = abs(x3 - x1)
                        if d1 < d2:
                            x1 = x
                        else:
                            x1 = x3
                        d1 = abs(x2 - x)
                        d2 = abs(x2 - x3)
                        if d1 < d2:
                            x2 = x
                        else:
                            x2 = x3
            values_c.append(x3)
            x3 = x2
            x2 = x1
            x1 = x
        values_c.append(x3)
        values_c.append(x2)
        values_c.append(x1)
        return values_c
    @staticmethod
    def negativeOneOnTail(values):
        values_copy = copy.deepcopy(values)
        flag = True
        while flag:
            lastValue = values_copy[-1]
            if values_copy[-1] != -1 and values_copy[-1]>0 and values_copy[-1]<1:
                flag = False
            else:
                values_copy.pop(-1)
        return values_copy

    @staticmethod
    def handleNegativeOne(values):
        values_copy = copy.deepcopy(values)
        values_copy = DataPreprocessing.negativeOneOnTail(values_copy)
        valuesWithoutZero = []
        lastValue = -2
        currentValue = -1
        nextValue = -1
        while len(values_copy)>0:
            numOfContinuousNegOne = 1
            currentValue = values_copy.pop(0)
            if len(values_copy)>0 :
                nextValue = values_copy[0]
            else:
                nextValue = currentValue
            while nextValue==-1 and currentValue==-1:
                values_copy.pop(0)
                numOfContinuousNegOne = numOfContinuousNegOne+1
                nextValue = values_copy[0]
            if currentValue == -1:
                if lastValue == -2:
                    for index in range(0, numOfContinuousNegOne):
                        valuesWithoutZero.append(nextValue)
                        currentValue = nextValue
                else:
                    for index in range(0, numOfContinuousNegOne):
                        valuesWithoutZero.append(((nextValue - lastValue) / (numOfContinuousNegOne + 1)) * (index + 1) + lastValue)
                        currentValue = ((nextValue - lastValue) / (numOfContinuousNegOne + 1)) * (numOfContinuousNegOne) + lastValue
            else:
                valuesWithoutZero.append(currentValue)
            lastValue = currentValue
        # valuesWithoutZero = DataPreprocessing.hf1(valuesWithoutZero)
        # valuesWithoutZero = DataPreprocessing.hf2(valuesWithoutZero)
        return  valuesWithoutZero
    @staticmethod
    # consider the time: differentiate blink and look away from screen
    # blink duartion is less than 400 ms
    def handleNegativeOneV2(values, flag):
        values_copy = copy.deepcopy(values)
        values_copy = copy.deepcopy(values)
        values_copy = DataPreprocessing.negativeOneOnTail(values_copy)
        valuesWithoutZero = []
        # some global variables
        bd = 400.0
        f = 60.0
        maxNum = int(bd /(1000.0/f)+ 0.5)
        # some helper variables
        lastNoneNegativeOneValue = -2 # just for initilization
        numNegativeOnesInARow = 0
        while len(values_copy) > 0:
            # pop the top one
            value = values_copy.pop(0)
            # if it is not -1
            if value != -1:# and value>0 and value<1:
                lastNoneNegativeOneValue = value
                valuesWithoutZero.append(value)
            # if it is -1
            else:
                numNegativeOnesInARow = numNegativeOnesInARow+1
                # peek next one to see if it is anotehr negative one
                while values_copy[0] == -1 or values_copy[0] <= 0 or values_copy[0] >= 1:
                    # pop it
                    values_copy.pop(0)
                    numNegativeOnesInARow = numNegativeOnesInARow+1
                # next non-negative one value
                nextValue = values_copy[0]
                # check whether it is look away case
                if numNegativeOnesInARow >= maxNum:
                    # look away case
                    for i in range(0, numNegativeOnesInARow):
                        valuesWithoutZero.append(-1)
                    # update variables
                    numNegativeOnesInARow = 0
                else:
                    # blink case
                    # case 1: on top
                    if lastNoneNegativeOneValue == -2:
                        for i in range(0, numNegativeOnesInARow):
                            valuesWithoutZero.append(nextValue)
                    # case 2: middle
                    else:
                        for index in range(0, numNegativeOnesInARow):
                            valuesWithoutZero.append(((nextValue - lastNoneNegativeOneValue) / (numNegativeOnesInARow + 1)) * (index + 1) + lastNoneNegativeOneValue)
                    # update
                    numNegativeOnesInARow = 0
        if flag:
            valuesWithoutZero = DataPreprocessing.hf1(valuesWithoutZero)
            valuesWithoutZero = DataPreprocessing.hf2(valuesWithoutZero)
        return valuesWithoutZero
    @staticmethod
    def correspondingXAndY(xs, ys):
        xs_new = []
        ys_new = []
        for i in range(0, len(xs)):
            x_v = xs[i]
            y_v = ys[i]
            if x_v <0 or y_v <0:
                xs_new.append(-1)
                ys_new.append(-1)
            else:
                xs_new.append(x_v)
                ys_new.append(y_v)
        return xs_new, ys_new

    @staticmethod
    def getOtherApplicationTime(at_kbAndM, application, name):
        at_otherApplication = []
        index = 0
        while index < len(at_kbAndM):
            if name not in application[index] and  application[index]!='0':
                # peek folowing
                index_peek = index+1
                while index_peek < len(at_kbAndM) and name not in application[index_peek]and  name!='0':
                    index_peek = index_peek + 1
                # index is equal to index_peek, which means the interval is too short and not be considered
                if index != index_peek:
                    at_otherApplication.append(at_kbAndM[index])
                    if index_peek == len(at_kbAndM):
                        index_peek = index_peek-1
                    at_otherApplication.append(at_kbAndM[index_peek])
                index = index_peek
            index = index+1
        return at_otherApplication

    @staticmethod
    def isInWantedApplication(time, at_otherApplication):
        p = Time.Time().findPositionInTimeArray(time, at_otherApplication)
        if p%2 == 1:
            return False
        else:
            return True

    @staticmethod
    def buildFixationFlagListFromEsacIndex(EsacIndex, rt_gaze, gazeX, gazeY):
        gazeType = []
        for i in range(0, len(rt_gaze)):
            if float(gazeX[i]) == -1.0:
                gazeType.append(2)
            else:
                if i in EsacIndex:
                    gazeType.append(1)
                else:
                    gazeType.append(0)
        refineGazeType = DataPreprocessing.postProcessingFixationFlagList(gazeType, rt_gaze, gazeX, gazeY)
        if len(refineGazeType) != len(gazeType):
            print("Error 1");
            sys.exit();
        return refineGazeType

    @staticmethod
    def postProcessingFixationFlagList(gazeType, rt_gaze, gazeX, gazeY):
        length = 1680
        width  = 1050
        # 2 things done by this method
            # first merge close fixations
            # then get rid of small fixations
        refineGazeType = []

        lastFixationLocation = [-1, -1] # [x_avg, y_avg]
        holdingPool = []

        x = np.array(gazeX)
        y = np.array(gazeY)
        # chunk by chunk
        lastChunk_b = -1
        while lastChunk_b < len(gazeType) - 1:
            chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeType)
            if c_type == 0:
                # check previous fixation location
                if lastFixationLocation[0] == -1:
                    if len(holdingPool)!=0:
                        refineGazeType.extend(holdingPool)
                        # refresh holding pool
                        holdingPool = []
                    for i in range(chunk_f, chunk_b + 1):
                        refineGazeType.append(0)
                    # update last fixation location
                    x_newfixation = x[chunk_f:chunk_b + 1] * length
                    y_newfixation = y[chunk_f:chunk_b + 1] * width
                    lastFixationLocation[0] = np.mean(x_newfixation)
                    lastFixationLocation[1] = np.mean(y_newfixation)

                else:
                    x_newfixation = x[chunk_f:chunk_b+1] * length
                    y_newfixation = y[chunk_f:chunk_b+1] * width
                    x_avg = np.mean(x_newfixation)
                    y_avg = np.mean(y_newfixation)
                    if ((x_avg - lastFixationLocation[0])**2+(y_avg - lastFixationLocation[1])**2)**(1/2) <= 25:
                        # belong to same fixation
                        for i in range(0, len(holdingPool)):
                            refineGazeType.append(0)
                        for i in range(chunk_f, chunk_b+1):
                            refineGazeType.append(0)
                            # refresh holding pool
                        holdingPool = []
                    else:
                        # 2 fixations
                        refineGazeType.extend(holdingPool)
                        holdingPool = []
                        for i in range(chunk_f, chunk_b+1):
                            refineGazeType.append(0)
                        # update last fixation location
                        lastFixationLocation[0] = np.mean(x_newfixation)
                        lastFixationLocation[1] = np.mean(y_newfixation)


            else:
                for i in range(chunk_f, chunk_b+1):
                    holdingPool.append(gazeType[i])
            # update
            lastChunk_b = chunk_b
        # append the last holding part
        if lastFixationLocation[0] == -1:
            if len(holdingPool) != 0:
                refineGazeType.extend(holdingPool)
        # last step is filter out short fixation
        return DataPreprocessing.filterOutShortFixtion(rt_gaze, refineGazeType)

    @staticmethod
    def filterOutShortFixtion (rt_gaze, gazeType):
        refineGazeType = []

        # chunk by chunk
        lastChunk_b = -1
        while lastChunk_b < len(gazeType) - 1:
            chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeType)

            if c_type == 0:
                dur = -1
                if chunk_f != 0:
                    dur = rt_gaze[chunk_b] - rt_gaze[chunk_f-1]
                else:
                    dur = rt_gaze[chunk_b] - rt_gaze[chunk_f]

                if dur < 100:
                    for i in range(chunk_f, chunk_b+1):
                        refineGazeType.append(3) # too short. neither saccade nor fixation
                else:
                    for i in range(chunk_f, chunk_b+1):
                        refineGazeType.append(0) # fixation
            else:
                # determine as saccade
                for i in range(chunk_f, chunk_b+1):
                    refineGazeType.append(gazeType[i]) # keep same
            # update
            lastChunk_b = chunk_b
        return refineGazeType
    @staticmethod
    def nextChunk(lastChunkIndex_b, gazeTypeList):
        currentType = int(gazeTypeList[lastChunkIndex_b + 1])
        chunk_f = lastChunkIndex_b + 1
        chunk_b = -1  # initailization
        for i in range(lastChunkIndex_b + 1, len(gazeTypeList)):
            if int(gazeTypeList[i]) != currentType:
                break
            chunk_b = i
        if chunk_b == -1:
            chunk_b = len(gazeTypeList)
        return chunk_f, chunk_b, currentType
    @staticmethod
    def typingSpeed(rt_kb):
        return float(len(rt_kb)) / (float(rt_kb[-1] - rt_kb[0]) / 1000.0)
    @staticmethod
    def persentageOfTypingWhileLookingAtKeyboard(gazeTypeList, rt_gaze, rt_kb, y_ratio):
        returnNumber = 0
        lastIndex_kb = 0
        # chunk by chunk
        lastChunk_b = -1
        while lastChunk_b < len(gazeTypeList) - 1:
            chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeTypeList)
            if c_type == 2:
                # do something
                a = y_ratio[chunk_f -1]
                b = y_ratio[chunk_f -2]
                # look down
                rt_f = rt_gaze[chunk_f]
                rt_b = rt_gaze[chunk_b]
                index_kb_f = Time.Time().findPositionInFloatList(rt_f, rt_kb,lastIndex_kb)
                if index_kb_f >= len(rt_kb):
                    break
                lastIndex_kb = index_kb_f
                index_kb_b = Time.Time().findPositionInFloatList(rt_b, rt_kb,lastIndex_kb-1)
                if index_kb_b>= len(rt_kb):
                    break
                lastIndex_kb = index_kb_b
                returnNumber += (index_kb_b-index_kb_f)
            # update
            lastChunk_b = chunk_b
        return float(returnNumber)/float(len(rt_kb))



