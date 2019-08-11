import numpy
import copy
import CsvReader
import Time
import DataPreprocessing
from scipy.spatial import distance
from scipy import stats
import math
from scipy.stats.stats import pearsonr

# basic class
# fixation class
class Fixation(object):
    # endIndex one more
    def __init__(self, isLoad = False, rt_trace=None, x_trace=None, y_trace=None, startRt=None, endRt=None, duration=None, fx=None, fy=None):
        if isLoad == False:
            self.start_rt =  rt_trace[0]
            self.end_rt = rt_trace[-1]
            self.duration = self.end_rt - self.start_rt
            self.fixation_x = numpy.mean(numpy.array(x_trace))
            self.fixation_y = numpy.mean(numpy.array(y_trace))
        else:
            self.start_rt = startRt
            self.end_rt = endRt
            self.duration = self.end_rt - self.start_rt
            self.fixation_x = fx
            self.fixation_y = fy


    def isLookAway(self):
        flag = False
        a = (self.x_trace < 0).sum() / float(self.x_trace.size)
        if (self.x_trace<0).sum()/float(self.x_trace.size) >= 0.8:
            flag = True
        return flag

    # threshold is 300 ms
    def isLongFixation(self, threshold = 350):
        if self.duration >= threshold:
            return True
        else:
            return False

# look-away class
class LookAway(object):
    def __init__(self, startRT, endRT,duration):
        self.startRt = startRT
        self.endRt = endRT
        self.duration = duration

# saccade class
class Saccade(object):

    # def __init__(self, lastFixation, currentFixation):
    #     self.start_t = lastFixation.end_t
    #     self.end_t = currentFixation.start_t
    #     self.start_p = (int(lastFixation.fixation_x), int(lastFixation.fixation_y))
    #     self.end_p = (int(currentFixation.fixation_x), int(currentFixation.fixation_y))
    #     self.distance = distance.euclidean(self.start_p, self.end_p)
    #     self.duration = self.end_t - self.start_t
    def __init__(self, start_p, end_p, start_t, end_t):
        self.start_p = (int(start_p[0]),int(start_p[1]))
        self.end_p = (int(end_p[0]),int(end_p[1]))
        self.duration = end_t - start_t
        self.distance = distance.euclidean(self.start_p, self.end_p)
        self.vector = numpy.array([end_p[0]-start_p[0],end_p[1]-start_p[1]])
    def getSaccdeDirection(self):
        degree = math.degrees(Saccade.angle_between_hz(self.vector))
        if math.degrees(Saccade.angle_between_vt(self.vector)) > 90:
            degree = 360 - degree
        return degree
    def getSaccadeType(self):
        degree = self.getSaccdeDirection()
        if (degree >=0 and degree <= 10) or (degree>=350):
            return 'forward'
        if degree >= 170 and degree <= 190:
            return 'backward'
        if degree >= 80 and degree <= 100:
            return 'upward'
        if degree >= 260 and degree <=280:
            return 'downward'
        return 'normal'

    # some static function used for compute saccade direction
    @staticmethod
    def unit_vector(vector):
        return vector / numpy.linalg.norm(vector)

    @staticmethod
    def angle_between_hz(v1):
        v2 = numpy.array([1.0, 0.0])
        v1_u = Saccade.unit_vector(v1)
        v2_u = Saccade.unit_vector(v2)
        return numpy.arccos(numpy.clip(numpy.dot(v1_u, v2_u), -1.0, 1.0))
    @staticmethod
    def angle_between_vt(v1):
        v2 = numpy.array([0.0, 1.0])
        v1_u = Saccade.unit_vector(v1)
        v2_u = Saccade.unit_vector(v2)
        return numpy.arccos(numpy.clip(numpy.dot(v1_u, v2_u), -1.0, 1.0))

# regressive saccade
class RegressiveSaccade(object):
    def __init__(self, saccade):
        self.start_p = saccade.start_p
        self.end_p = saccade.end_p
        self.duration = saccade.duration
        self.distance = saccade.distance
        self.speed = self.distance / self.duration

# pursuit class
class Pursuit(object):
    def __init__(self, x_trace, y_trace, time_trace):
        self.duration = time_trace[-1] - time_trace[0]
        self.distance = distance.euclidean((x_trace[0], y_trace[0]),(x_trace[-1], y_trace[-1]))
        self.start_p = (int(x_trace[0]), int(y_trace[0]))
        self.end_p = (int(x_trace[-1]), int(y_trace[-1]))
        self.displacement = 0
        self.x_trace = numpy.array(x_trace)
        for i in range(1, len(x_trace)):
            self.displacement += distance.euclidean((x_trace[i-1], y_trace[i-1]), (x_trace[i], y_trace[i]))
    def isLookAway(self):
        flag = False
        a = (self.x_trace < 0).sum() / float(self.x_trace.size)
        if (self.x_trace<0).sum()/float(self.x_trace.size) >= 0.8:
            flag = True
        return flag
# look away class
# class LookAway(object):
#     def __init__(self, startRT,  endRT):
#         self.duration = endRT - startRT


def reverseRTList(rt):
    # copy first
    rt_c = copy.deepcopy(rt)
    rt_c = rt_c[::-1]
    rt_r_np = numpy.array(rt_c) - rt[-1]
    rt_r_np = numpy.absolute(rt_r_np)
    rt_r = rt_r_np.tolist()
    return rt_r
# chunk index finder
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

def reformatEList(E):
    E_1d = []
    for lt in E:
        E_1d.append(lt[0])
        E_1d.append(lt[1])
    return  E_1d

def findPositionInFloatList(value, l):
    position = 0
    while value >= l[position]:
        position = position+1
        if position >= len(l):
            return len(l)
    return position

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

def postProcessingUndefineRefine(gazeType):
    refineGazeType = []
    # chunk by chunk
    lastChunk_b = -1
    lastChunkType = -5 # just for initialization
    while lastChunk_b < len(gazeType) - 1:
        chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeType)
        if c_type == 0:
            lastChunkType = 0
            for i in range(chunk_f, chunk_b + 1):
                refineGazeType.append(0)
        elif c_type == 1:
            lastChunkType =1
            for i in range(chunk_f, chunk_b + 1):
                refineGazeType.append(1)
        elif c_type == 3:
            length = chunk_b - chunk_f + 1
            if lastChunkType == -5 or lastChunkType == 1:
                # peek next chunk
                nextChunkStartIndex = chunk_b +1
                if nextChunkStartIndex < len(gazeType) - 1 and gazeType[nextChunkStartIndex] == 1 and length<=6:
                    for i in range(chunk_f, chunk_b + 1):
                        refineGazeType.append(1)
                        lastChunkType = 1
                else:
                    for i in range(chunk_f, chunk_b + 1):
                        refineGazeType.append(3)
                        lastChunkType = 3
        lastChunk_b = chunk_b
    return  refineGazeType

def postProcessingFixationFlagList(gazeType, rt_gaze, gazeX, gazeY):
    # 2 things done by this method
        # first merge close fixations
        # then get rid of small fixations
    refineGazeType = []

    lastFixationLocation = [-1, -1] # [x_avg, y_avg]
    holdingPool = []

    x = numpy.array(gazeX)
    y = numpy.array(gazeY)
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
                x_newfixation = x[chunk_f:chunk_b + 1]
                y_newfixation = y[chunk_f:chunk_b + 1]
                lastFixationLocation[0] = numpy.mean(x_newfixation)
                lastFixationLocation[1] = numpy.mean(y_newfixation)

            else:
                x_newfixation = x[chunk_f:chunk_b+1]
                y_newfixation = y[chunk_f:chunk_b+1]
                x_avg = numpy.mean(x_newfixation)
                y_avg = numpy.mean(y_newfixation)
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
                    lastFixationLocation[0] = numpy.mean(x_newfixation)
                    lastFixationLocation[1] = numpy.mean(y_newfixation)
        else:
            for i in range(chunk_f, chunk_b+1):
                holdingPool.append(gazeType[i])
        # update
        lastChunk_b = chunk_b
    # append the last holding part
    if lastFixationLocation[0] == -1:
        if len(holdingPool) != 0:
            refineGazeType.extend(holdingPool)
    return refineGazeType

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

def IVDT_MP(x, y, x_raw, y_raw, time, tfix, dmax, minvel, corr):
    """
        Detects fixations, saccades and smooth pursuit also not look at screen
        Decoding rules:
            0: fixation
            1: saccade
            3: undefine
            4: smooth pursuit
    """
    # gazeTypeList_ivt: 0: fixation, 1: saccade, 2: not look at screen, 3 undefine
    gazeTypeList_ivt = IVT_withPostProcessing(x, y, time, minvel)
    # # gazeTypeList
    # gazeTypeList = []
    # # find smooth pursuit
    # lastChunk_b = -1
    # while lastChunk_b < len(gazeTypeList_ivt) - 1:
    #     chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeTypeList_ivt)
    #     if c_type != 0:
    #         # not fixation
    #         gazeTypeList.extend(gazeTypeList_ivt[chunk_f:chunk_b+1])
    #     else:
    #         # try to find SP
    #         x_part = x[chunk_f:chunk_b+1]
    #         y_part = y[chunk_f:chunk_b+1]
    #         x_raw_part = x_raw[chunk_f:chunk_b + 1]
    #         y_raw_part = y_raw[chunk_f:chunk_b + 1]
    #         time_part = time[chunk_f:chunk_b+1]
    #         # call IDT
    #         # EfixTuple format:[..., (fixationStartIndex, fixationEndIndex{one more}),...]
    #         _, EfixIndex, EfixTuple = fixation_IDT_V2(x_part, y_part, time_part,tfix=tfix, dmax=dmax)
    #         EfixIndex = mp(x_raw_part, y_raw_part, EfixIndex, EfixTuple, corr)
    #         for i in range(chunk_f, chunk_b+1):
    #             c = i-chunk_f
    #             if c not in EfixIndex:
    #                 gazeTypeList.append(4)
    #             else:
    #                 gazeTypeList.append(0)
    #     #  update
    #     lastChunk_b = chunk_b
    return gazeTypeList_ivt

def mp(x_part, y_part, EfixIndex, EfixTuple, corr):
    EfixIndex_np = numpy.array(EfixIndex)
    for t in EfixTuple:
        cor = computeCorralation(x_part[t[0]:t[1]], y_part[t[0]:t[1]])
        if numpy.abs(cor[0]) >= corr:
            # SP
            pursuitIndex = numpy.arange(t[0], t[1]).tolist()
            EfixIndex_np = numpy.delete(EfixIndex_np, pursuitIndex)

        # check
        # with open('C:\\Users\\JW\\Desktop\\tif\\tif_chi\\alpha.csv', "a") as myfile:
        #     myfile.write(str(numpy.abs(cor[0])))
        #     myfile.write('\n')
        #

        # if (t[1] - t[0]) > windowS:
        #     numIter = int(float(t[1] - t[0]) / windowS)
        #     for iIter in range(0, numIter-1):
        #         s = iIter * windowS + t[0]
        #         e = s + windowS + t[0]
        #         avgDistance = computeDistanceOfMxAndMy(x_part[s:e], y_part[s:e])
        #         # check
        #         with open('C:\\Users\\JW\\Desktop\\tif\\tif_chi\\alpha.csv', "a") as myfile:
        #             myfile.write(str(avgDistance))
        #             myfile.write('\n')
        #         #
        #     # last round
        #     s_c = (numIter-1)*windowS
        #     avgDistance = computeDistanceOfMxAndMy(x_part[(numIter-1)*windowS:t[1]], y_part[(numIter-1)*windowS:t[1]])
        #     # check
        #     with open('C:\\Users\\JW\\Desktop\\tif\\tif_chi\\alpha.csv', "a") as myfile:
        #         myfile.write(str(avgDistance))
        #         myfile.write('\n')
        #     #

    #     alpha_dev = angleStandardDeviation(x_part[t[0]:t[1]], y_part[t[0]:t[1]])
    #     if alpha_dev <= t_alphaDev:
    #         pursuitIndex = numpy.array(t[0], t[1]).tolist()
    #         # if it is pursuit then remove them
    #         EfixIndex_np = numpy.delete(EfixIndex_np, pursuitIndex)
    EfixIndex = EfixIndex_np.tolist()
    return EfixIndex

def computeCorralation(x_part, y_part):
    return  pearsonr(x_part, y_part)

def computeDistanceOfMxAndMy(x_window, y_window):
    x_unitCircle = []
    y_unitCircle = []
    for i in range(1, len(x_window)):
        v_x = x_window[i] - x_window[i-1]
        v_y = y_window[i] - y_window[i-1]
        if  not (v_x == 0 and v_y == 0):
            v_x = float(v_x) / distance.euclidean((v_x, v_y), (0, 0))
            v_y = float(v_y) / distance.euclidean((v_x, v_y), (0, 0))
            x_unitCircle.append(v_x)
            y_unitCircle.append(v_y)
    if len(x_unitCircle) == 0 or len(y_unitCircle)==0:
        print('d')
    return distance.euclidean((numpy.mean(numpy.array(x_unitCircle)), numpy.mean(numpy.array(y_unitCircle))), (0, 0))

def fixation_detection(x, y, time, missing=0.0, maxdist=80, mindur=180):
    """Detects fixations, defined as consecutive samples with an inter-sample
    distance of less than a set amount of pixels (disregarding missing data)

    arguments

    x		-	numpy array of x positions
    y		-	numpy array of y positions
    time		-	numpy array of EyeTribe timestamps

    keyword arguments

    missing	-	value to be used for missing data (default = 0.0)
    maxdist	-	maximal inter sample distance in pixels (default = 25)
    mindur	-	minimal duration of a fixation in milliseconds; detected
                fixation cadidates will be disregarded if they are below
                this duration (default = 100)

    returns
    Sfix, Efix
                Sfix	-	list of lists, each containing [starttime]
                Efix	-	list of lists, each containing [starttime, endtime, duration, endx, endy]
    """
    # holder
    EfixIndex = []

    # empty list to contain data
    Sfix = []
    Efix = []

    # loop through all coordinates
    si = 0
    fixstart = False
    for i in range(1, len(x)):
        # calculate Euclidean distance from the current fixation coordinate
        # to the next coordinate
        dist = ((x[si] - x[i]) ** 2 + (y[si] - y[i]) ** 2) ** 0.5
        # check if the next coordinate is below maximal distance
        if dist <= maxdist and not fixstart:
            # start a new fixation
            si = 0 + i
            fixstart = True
            Sfix.append([time[i]])
        elif dist > maxdist and fixstart:
            # end the current fixation
            fixstart = False
            # only store the fixation if the duration is ok
            #debug = time[i - 1] - Sfix[-1][0]
            if time[i - 1] - Sfix[-1][0] >= mindur:
                Efix.append([Sfix[-1][0], time[i - 1], time[i - 1] - Sfix[-1][0], x[si], y[si]])
                EfixIndex.append(si)
                EfixIndex.append((i-1))
            # delete the last fixation start if it was too short
            else:
                Sfix.pop(-1)
            si = 0 + i
        elif not fixstart:
            si += 1


    return reformatEList(Efix), EfixIndex

def saccade_detection(x, y, time, missing=0.0, minlen=10, maxvel=1485, maxacc=340):
    """Detects saccades, defined as consecutive samples with an inter-sample
    velocity of over a velocity threshold or an acceleration threshold

    arguments
    x		-	numpy array of x positions
    y		-	numpy array of y positions
    time		-	numpy array of tracker timestamps in milliseconds
    keyword arguments
    missing	-	value to be used for missing data (default = 0.0)
    minlen	-	minimal length of saccades in milliseconds; all detected
                saccades with len(sac) < minlen will be ignored
                (default = 5)
    maxvel	-	velocity threshold in pixels/second (default = 40)
    maxacc	-	acceleration threshold in pixels / second**2
                (default = 340)

    returns
    Ssac, Esac
            Ssac	-	list of lists, each containing [starttime]
            Esac	-	list of lists, each containing [starttime, endtime, duration, startx, starty, endx, endy]
    """
    # holder
    EsacIndex = []
    # CONTAINERS
    Ssac = []
    Esac = []

    # INTER-SAMPLE MEASURES
    # the distance between samples is the square root of the sum
    # of the squared horizontal and vertical interdistances
    intdist = (numpy.diff(x) ** 2 + numpy.diff(y) ** 2) ** 0.5
    # get inter-sample times
    inttime = numpy.diff(time)
    # recalculate inter-sample times to seconds
    inttime = inttime / 1000.0

    # VELOCITY AND ACCELERATION
    # the velocity between samples is the inter-sample distance
    # divided by the inter-sample time
    vel = intdist / inttime
    # the acceleration is the sample-to-sample difference in
    # eye movement velocity
    acc = numpy.diff(vel)

    # SACCADE START AND END
    t0i = 0
    stop = False
    while not stop:
        # saccade start (t1) is when the velocity or acceleration
        # surpass threshold, saccade end (t2) is when both return
        # under threshold

        # detect saccade starts
        sacstarts = numpy.where((vel[1 + t0i:] > maxvel).astype(int) == 1)[0]
        if len(sacstarts) > 0:
            # timestamp for starting position
            t1i = t0i + sacstarts[0] + 1
            if t1i >= len(time) - 1:
                t1i = len(time) - 2
            t1 = time[t1i]

            # add to saccade starts
            Ssac.append([t1])

            # detect saccade endings
            sacends = numpy.where((vel[1 + t1i:] < maxvel).astype(int) == 1)[0]
            if len(sacends) > 0:
                # timestamp for ending position
                t2i = sacends[0] + 1 + t1i #+ 2
                if t2i >= len(time):
                    t2i = len(time) - 1
                t2 = time[t2i]
                dur = t2 - t1

                # ignore saccades that did not last long enough
                if dur >= minlen:
                    # add to saccade ends
                    Esac.append([t1, t2, dur, x[t1i], y[t1i], x[t2i], y[t2i]])
                    for i in range(t1i, t2i):
                        EsacIndex.append(i+1)
                else:
                    # remove last saccade start on too low duration
                    Ssac.pop(-1)

                # update t0i
                t0i = 0 + t2i
            else:
                stop = True
        else:
            stop = True

    return reformatEList(Esac), EsacIndex

def IVT_withPostProcessing(x, y, time, minvel):
    # some preparing
    x_r = copy.deepcopy(x)
    x_r = x_r[::-1]
    y_r = copy.deepcopy(y)
    y_r = y_r[::-1]
    time_r = reverseRTList(time)
    _, EsacIndex = saccade_detection(x, y, time, maxvel=minvel)
    # gazeTypeList decoding rules: 0 is fixation, 1 is saccade, 2 is not look at screen
    gazeTypeList_temp = buildFixationFlagListFromEsacIndex(EsacIndex, time, x, y)
    # --- filter ---
    gazeTypeList_temp = postProcessingFixationFlagList(gazeTypeList_temp, time, x, y)
    gazeTypeList_temp = gazeTypeList_temp[::-1]
    gazeTypeList_temp = postProcessingFixationFlagList(gazeTypeList_temp, time_r, x_r, y_r)
    # reverse back
    gazeTypeList_ivt = gazeTypeList_temp[::-1]
    # take care -1 3 3 -1 case


    gazeTypeList_ivt = filterOutShortFixtion(time,gazeTypeList_ivt)
    return postProcessingUndefineRefine(gazeTypeList_ivt)
    #return gazeTypeList_ivt

def fixation_IDT(x, y, time, tfix = 180, dmax = 80):
    Efix1D = []
    EfixIndex = []
    i = 0
    while i < len(x):
        o = [x[i], y[i]]
        maxX = o[0]
        minX = o[0]
        maxY = o[1]
        minY = o[1]
        j = 1
        while j+i < len(x):
            next = [x[i+j], y[i+j]]
            if next[0] > maxX:
                maxX = next[0]
            if next[0] < minX:
                minX = next[0]
            if next[1] > maxY:
                maxY = next[1]
            if next[1] < minY:
                minY = next[1]
            d = (maxX - minX)+(maxY - minY)
            if d > dmax:
                break
            j = j+1
        position = i+j-1
        if position >= len(x):
            position = position-1
        if position < 0:
            position = 0
        if time[position] - time[i] > tfix:
            Efix1D.append(time[i])
            Efix1D.append(time[position])
            EfixIndex.append(i)
            EfixIndex.append(position)
            start_index = i
            for index in range(start_index, position):
                i = i+1
        else:
            i = i+1
    return Efix1D, EfixIndex

def fixation_IDT_V2(x, y, time, tfix = 180, dmax = 80):
    Efix1D = []
    EfixIndex = []
    EfixTuple =[]
    i = 0
    while i < len(x):
        o = [x[i], y[i]]
        maxX = o[0]
        minX = o[0]
        maxY = o[1]
        minY = o[1]
        j = 1
        while j+i < len(x):
            next = [x[i+j], y[i+j]]
            if next[0] > maxX:
                maxX = next[0]
            if next[0] < minX:
                minX = next[0]
            if next[1] > maxY:
                maxY = next[1]
            if next[1] < minY:
                minY = next[1]
            d = (maxX - minX)+(maxY - minY)
            if d > dmax:
                break
            j = j+1
        position = i+j-1
        if position >= len(x):
            position = len(x)
        if position < 0:
            position = 0
        if time[position] - time[i] > tfix:
            Efix1D.append(time[i])
            Efix1D.append(time[position])
            # EfixIndex.append(i)
            # EfixIndex.append(position)
            EfixTuple.append((i, position))
            for addingIndex in range(i, position):
                EfixIndex.append(addingIndex)
            start_index = i
            for index in range(start_index, position):
                i = i+1
        else:
            i = i+1
    return Efix1D, EfixIndex, EfixTuple

def lookDownToKeyboard_detection(x, y, r_t, Esac_1d):
    # x, y are coordinates of eyegaze
    # r_t is relative time
    # Esac_1d is generated from last step
    El2kb_1d = []
    lastIndex = -1
    for i in range(0, len(r_t)):
        if y[i] >= 0.9:
            lastIndex = i
            # now check whether it is in saccade period
            p = findPositionInFloatList(r_t[i], Esac_1d)
            if p%2 == 1:
                # is in saccade
                if Esac_1d[p-1] not in El2kb_1d:
                    El2kb_1d.append(Esac_1d[p-1])
                    El2kb_1d.append(Esac_1d[p])
    return El2kb_1d

def determineGazeStatus(timeOfRelative, E_f_1d, E_s_1d):
    position_fixation = findPositionInFloatList(timeOfRelative, E_f_1d)
    position_saccade = findPositionInFloatList(timeOfRelative, E_s_1d)
    # check whether it is fixation
    if position_fixation%2 == 1 and position_fixation != -1:
        return 0 # fixation
    elif position_saccade%2 == 1 and position_saccade != -1:
        return 1 # saccade
    else:
        return 2

def determineGazeStatusV2(timeOfRelative, E_f_1d):
    position_fixation = findPositionInFloatList(timeOfRelative, E_f_1d)
    # check whether it is fixation
    if position_fixation%2 == 1 and position_fixation != -1:
        return 0 # fixation
    else:
        return 1 # saccade

def determineGazeStatusV3(timeOfRelative, E_s_1d):
    position_fixation = findPositionInFloatList(timeOfRelative, E_s_1d)
    # check whether it is fixation
    if position_fixation%2 == 1 and position_fixation != -1:
        return 1 # saccade
    else:
        return 0 # fixation

def isLookingDownToKeyboard(rt, El2kb_1d):
    p = findPositionInFloatList(rt, El2kb_1d)
    if p%2 == 1:
        return True

# drawing part
def create_blank(width, height, rgb_color=(0, 0, 0)):
    """Create new image(numpy array) filled with certain color in RGB"""
    # Create black blank image
    image = numpy.zeros((height, width, 3), numpy.uint8)
    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color
    return image

def drawGaze(x, y, gazeType, height_window):
    frame = create_blank(len(x), height_window, (255, 255, 255))
    # draw state
    lastChunk_b = -1
    while lastChunk_b < len(gazeType) - 1:
        chunk_f, chunk_b, c_type = DataPreprocessing.nextChunk(lastChunk_b, gazeType)
        if c_type == 1:
            #saccade -- yellow
            frame[:, chunk_f:chunk_b+1] = [255,255,0]
        if c_type == 4:
            #pursuit -- green
            frame[:, chunk_f:chunk_b + 1] = [0, 255, 255]
        if c_type == 3:
            #noise -- red
            frame[:, chunk_f:chunk_b + 1] = [255, 0, 0]

        # update
        lastChunk_b = chunk_b
    # draw x, y
    for index in range(0,len(x)):
        width = 1680
        height = 1050
        x_p = int((x[index] / width) * height_window)
        y_p = int((y[index] / height) * height_window)
        cv2.circle(frame, (index, -1*(x_p-height_window)), 1, (80,50,200),-1)
        cv2.circle(frame, (index, -1*(y_p-height_window)), 1, (0, 0, 0), -1)
    return frame