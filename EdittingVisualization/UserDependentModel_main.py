# import library
import cv2
from glob import glob
import numpy as np
import  Time
import CsvReader
import ConvertTimeDomainToVideo
import DataPreprocessing
import Editting
import Visualization
import FeaturesAroundEditing
from pathlib import Path
import GazeMovement
import random

SEED = 448

def getAllFile(age_wanted):
    fileDirs = []
    fileMarks = [[],[],[]] # format: age group, task id, subjectID
    subjectID = 0
    for age in age_wanted:
        rootDir = 'C:\\Users\\csjunwang\\Desktop\\BeijingData_v2\\' + str(age) + '\\*\\'
        statDir = 'C:\\Users\\csjunwang\\Desktop\\BeijingData_v2\\' + str(age) + '\\'
        d = glob(rootDir)
        if(len(d)==0):
            continue
        for rd in d:
            for i in range(1,4):
                dir = rd + "t" + str(i) + "\\"
                # adding to list
                fileDirs.append(dir)
                fileMarks[0].append(int(age))
                fileMarks[1].append(int(i))
                fileMarks[2].append(int(subjectID))
            subjectID = subjectID+1
    return fileDirs, fileMarks

def fvsToArff(fileName, fvs, lbs, classmark, typeInstances):
    # instances  -> list
    # typeInstances -> string
    numAttributes = len(fvs[0])
    f = open(fileName, 'w')
    f.write("@RELATION " + typeInstances + "\n")
    for i in range(0, numAttributes):
        f.write('@ATTRIBUTE attri' + str(i) + ' NUMERIC\n')
    f.write('@ATTRIBUTE class ' + classmark + '\n')
    f.write('@DATA\n')
    for i in range(0, len(fvs)):
        fv = fvs[i]

        line = ""
        for v in fv:
            line += str(v)
            line += ','
        line+=lbs[i]

        f.write(line)
        f.write('\n')
    f.closed

class ConfusionMatrix(object):
    def __init__(self, numClass, numInstanceEachClass, lbs_list):
        self.lbs_list = lbs_list
        self.numClass = numClass
        self.numInstanceEachClass = numInstanceEachClass
        self.cm = []
        for i in range(0, numClass):
            temp = []
            for j in range(0, numClass):
                temp.append(0)
            self.cm.append(temp)
    def appendResult(self, reals, predicts):
        for i in range(0, len(reals)):
            r = reals[i]
            p = predicts[i]
            row_i = self.lbs_list.index(r)
            col_i = self.lbs_list.index(p)
            self.cm[row_i][col_i] += 1

    def print2console(self):
        print (str(self.cm))

def CrossValidation(FVs, LBs, GNum):
    orders = np.arange(len(FVs)).tolist()
    random.seed()
    orders = random.shuffle(orders)
    GLen = int(len(fvs)/GNum)
    Groups_FVs = []
    Groups_LBs = []
    count = 0
    for i in range(0, len(GNum)-1):
        temp_FVs = []
        temp_LBs = []
        for j in range(0, GLen):
            fetchI = orders[int(GLen*i + j)]
            temp_FVs.append(FVs[fetchI])
            temp_LBs.append(LBs[fetchI])
            # update count
            count += 1

        Groups_FVs.append(temp_FVs)
        Groups_LBs.append(temp_LBs)
    temp_FVs = []
    temp_LBs = []
    for k in range(count, len(FVs)):
        fetchI = orders[k]
        temp_FVs.append(FVs[fetchI])
        temp_LBs.append(LBs[fetchI])
    Groups_FVs.append(temp_FVs)
    Groups_LBs.append(temp_LBs)
# main function
# arg
arg_regenerate_editing_interval = True
length = 1680.0
width = 1050.0
fileDirs, fileMarks = getAllFile([1]) # only extract college data
# iterate all task
for i_file in range(0, len(fileDirs)):
    dir = fileDirs[i_file]
    # get csv file
    if len(glob(dir + '*gaze*.csv'))==0:
        continue
    csv1 = CsvReader.CsvReader(glob(dir + '*gaze*.csv')[0])
    if len(glob(dir + '*window*.csv'))==0:
        continue
    csv2 = CsvReader.CsvReader(glob(dir + 'window*.csv')[0])
    # extract gaze data
    data_gaze = csv1.getData([0, 2, 3], hasHeader=1, needHandleNegativeOneIndex=[2, 3], flag=True)
    # get rid of zeros
    if len(data_gaze[1]) != len(data_gaze[2]):
        data_gaze[0] = data_gaze[0][0:min(len(data_gaze[1]), len(data_gaze[2]))]
        data_gaze[1] = data_gaze[1][0:min(len(data_gaze[1]), len(data_gaze[2]))]
        data_gaze[2] = data_gaze[2][0:min(len(data_gaze[1]), len(data_gaze[2]))]
    # assign outside fixations to (-1, -1)
    data_gaze[1], data_gaze[2] = DataPreprocessing.DataPreprocessing().correspondingXAndY(data_gaze[1], data_gaze[2])
    # read video csv
    data_video = csv2.getData([0, 1], hasHeader=0, needHandleNegativeOneIndex=[], flag=False)
    # get absolute time for both video and gaze
    at_gaze = [Time.Time(i) for i in data_gaze[0]]
    at_video = [Time.Time(i) for i in data_video[1]]
    # interpolation to video
    start_v, end_v, data_gaze_videoTimeDomain = ConvertTimeDomainToVideo.ConvertTimeDomainToVideo().convertTimeDomain2Video(time_other=at_gaze, time_vidoe=at_video, collections_data=data_gaze[1:len(data_gaze)])
    if end_v == -1:
        end_v = len(data_video[0]) - 1
    full_gaze_at, full_gaze_data = ConvertTimeDomainToVideo.ConvertTimeDomainToVideo().InsertInterpolateListBack(at_video[start_v:end_v], at_gaze, data_gaze_videoTimeDomain, data_gaze[1:len(data_gaze)])
    # get cursor position info
    csv3 = CsvReader.CsvReader(glob(dir + '*newCursor*.csv')[0])
    data_cursor = csv3.getData([0, 1, 2], hasHeader=1, needHandleNegativeOneIndex=[], flag=True)
    ats_cursor = [Time.Time(at) for at in data_cursor[0]]
    xs_cursor = [float(x) for x in data_cursor[1]]
    ys_cursor = [float(y) for y in data_cursor[2]]
    # read keyboard info
    csv4 = CsvReader.CsvReader(glob(dir + '*mouse*.csv')[0])
    data_keyboard = csv4.getData([0, 2, 3], hasHeader=1, needHandleNegativeOneIndex=[], flag=True)
    ats_keyboard = [Time.Time(at) for at in data_keyboard[0]]
    info_types = data_keyboard[1]
    keypressInfo = data_keyboard[2]
    # refine
    refine_ats_keypresses, refine_keypresses_info = refineKeyboardInfoInGivenAtInterval(ats_keyboard, info_types, keypressInfo)
    # refine cursor info
    i_cursor_start = Time.Time().findPositionInTimeArray(refine_ats_keypresses[1], ats_cursor)
    ats_cursor = ats_cursor[i_cursor_start:]
    xs_cursor = xs_cursor[i_cursor_start:]
    ys_cursor = ys_cursor[i_cursor_start:]
    # read writing position info
    if len(glob(dir + '*writing*.csv')) == 0:
        continue
    csv5 = CsvReader.CsvReader(glob(dir + '*writing*.csv')[0])
    data_wp = csv5.getData([0, 1, 2], hasHeader=0, needHandleNegativeOneIndex=[], flag=True)
    ats_wp = [Time.Time(at) for at in data_wp[0]]
    xs_wp = [float(at) for at in data_wp[1]]
    ys_wp = [float(at) for at in data_wp[2]]
    # create writing position module and cursor position module
    WPM = Editting.WritingPositionModule(ats_wp, xs_wp, ys_wp)
    CPM = Editting.CursorPositionModule(ats_cursor, xs_cursor, ys_cursor)

    # delta t -- sliding window size
    DeltaT = 500  # 500 ms
    # extracting editing & nonEditing interval --------------------------------------------------
    editingFileName = dir + 'editing_interval.csv'
    nonEditingFileName = dir + 'nonEditing_interval.csv'
    editing_file = Path(editingFileName)
    nonEditing_file = Path(nonEditingFileName)
    isExist_ef = editing_file.is_file()
    if isExist_ef and (arg_regenerate_editing_interval == False):
        editingInterval, editingType = Editting.readEditingIntervalsCSV(editingFileName)
        nonEditingInterval = Editting.readNonEditingIntervalsCSV(nonEditingFileName)
    else:
        # editing
        EdittingModule = Editting.EditingModule(ats_cursor, xs_cursor, ys_cursor, WPM)
        EdittingModule.generate2CSV(dir + 'editing_interval.csv')
        editingInterval = EdittingModule.FullEdittingIntervals
        editingType = EdittingModule.editingTypes
        # nonEditing
        nonEditingModule = Editting.NonEditingModuleV2(refine_ats_keypresses, refine_keypresses_info)
        # extract nonEditing interval
        nonEditingInterval = nonEditingModule.Extract_nonEditing_Intervals(DeltaT, refine_ats_keypresses[0])
        nonEditingModule.generate2CSV(dir + 'nonEditing_interval.csv')

    # Extracting features -----------------------------------------------------------------------
    # user dependent
    FVs = []
    LBs = []
    FAE = FeaturesAroundEditing.FeaturesAheadEditingPointModule(
        ats_gaze=at_gaze,
        xs_gaze=[float(n) * 1680 for n in data_gaze[1]],
        ys_gaze=[float(n) * 1050 for n in data_gaze[2]],
        ats_kb=refine_ats_keypresses,
        keyInfo_kb=refine_keypresses_info,
        editingAtRange=editingInterval,
        editingType=editingType,
        caretATs=ats_cursor,
        caretXs=xs_cursor,
        caretYs=ys_cursor,
        writingPositionATs=ats_wp,
        writingPositionXs=xs_wp,
        writingPositionYs=ys_wp,
        deltaT = DeltaT
    )
    FANE = FeaturesAroundEditing.FeaturesAheadEditingPointModule(
        ats_gaze=at_gaze,
        xs_gaze=[float(n) * 1680 for n in data_gaze[1]],
        ys_gaze=[float(n) * 1050 for n in data_gaze[2]],
        ats_kb=refine_ats_keypresses,
        keyInfo_kb=refine_keypresses_info,
        editingAtRange=nonEditing.nonEditingIntervals,
        editingType=nonEditing.nonEditingTypes,
        caretATs=ats_cursor,
        caretXs=xs_cursor,
        caretYs=ys_cursor,
        writingPositionATs=ats_wp,
        writingPositionXs=xs_wp,
        writingPositionYs=ys_wp,
        non=True
    )
    FVs.extend(FAE.fvs)
    FVs.extend(FANE.fvs)
    LBs.extend(FAE.fv_name)
    LBs.extend(FANE.fv_name)
    # to csv
    fvsToArff(dir + 'efv.arff', FVs, LBs, '{Deletion, Insertion, nonEditing}', 'edit')





















