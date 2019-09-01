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
from pyod.models.auto_encoder import *
from pyod.models.knn import *

SEED = 448

def refineKeyboardInfoInGivenAtInterval(ats, info_types, keypressInfo):
    refine_ats = []
    refine_keypresses = []
    for i in range(0, len(ats)):
        # checking type
        type = info_types[i]
        if type == 'KeyboardDown':
            refine_ats.append(ats[i])
            refine_keypresses.append(keypressInfo[i])
    return refine_ats, refine_keypresses

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


def getAllFileUserBased(age_wanted):
    fileDirs = []
    subNames = []
    for age in age_wanted:
        rootDir = 'C:\\Users\\csjunwang\\Desktop\\BeijingData_v2\\' + str(age) + '\\*\\'
        statDir = 'C:\\Users\\csjunwang\\Desktop\\BeijingData_v2\\' + str(age) + '\\'
        d = glob(rootDir)
        if (len(d) == 0):
            continue
        for rd in d:
            sub_temp = []
            for i in range(1, 4):
                dir = rd + "t" + str(i) + "\\"
                # adding to list
                sub_temp.append(dir)
            name = rd.split('\\')[-2]
            fileDirs.append(sub_temp)
            subNames.append(name)
    return fileDirs, subNames


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
    def __init__(self, numClass, lbs_list):
        self.lbs_list = lbs_list
        self.numClass = numClass
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

def kNN_module(TrainingDs, TrainingLBs, TestingDs, TestingLBs, cfm):
    contamination = (len(TrainingLBs) - TrainingLBs.count('nonEditing')) / len(TrainingLBs)
    knn = KNN(
        contamination = contamination,
    )
    knn.fit(TrainingDs)
    predicts = knn.predict(TestingDs)
    reals = preprocessReals(TestingLBs)
    cfm.appendResult(reals, predicts)
def auto_encoder_module(TrainingDs, TrainingLBs, TestingDs, TestingLBs, cfm):
    contamination = (len(TrainingLBs) - TrainingLBs.count('nonEditing'))/len(TrainingLBs)

    AE = AutoEncoder(
        hidden_neurons= [int(len(TrainingDs[0])/2),int(len(TrainingDs[0])/4),int(len(TrainingDs[0])/4),int(len(TrainingDs[0])/2)],
        epochs=2000
    )

    AE.fit(TrainingDs)

    predicts = AE.predict(TestingDs)
    reals = preprocessReals(TestingLBs)
    cfm.appendResult(reals, predicts)

def preprocessReals(reals):
    refine = []
    for i in range(0, len(reals)):
        r = reals[i]
        if r == 'nonEditing':
            refine.append(0)
        else:
            refine.append(1)
    return refine


def CrossValidation(FVs, LBs, GNum, cfm):
    # build training data
    orders = np.arange(len(FVs)).tolist()
    random.seed()
    random.shuffle(orders)
    GLen = int(len(FVs)/GNum)
    Groups_FVs = []
    Groups_LBs = []
    count = 0
    for i in range(0, (GNum)-1):
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
    # iterate
    for i in range(0, GNum):
        # constructing training and testing dataset
        # ith group data as testing data
        trainingDs = []
        trainingLBs = []
        testingDs = []
        testingLBs = []
        for j in range(0, GNum):
            if j == i:
                testingDs.extend(Groups_FVs[j])
                testingLBs.extend(Groups_LBs[j])
            else:
                trainingDs.extend(Groups_FVs[j])
                trainingLBs.extend(Groups_LBs[j])
        # refine
        trainingDs_r = []
        trainingLBs_r = []
        for j in range(0, len(trainingLBs)):
            if trainingLBs[j] == 'nonEditing':
                trainingDs_r.append(trainingDs[j])
                trainingLBs_r.append(trainingLBs[j])
        # call pyod module
        auto_encoder_module(
            TrainingDs = trainingDs_r,
            TrainingLBs = trainingLBs_r,
            TestingDs = testingDs,
            TestingLBs = testingLBs,
            cfm = cfm
        )
        # kNN_module(
        #     TrainingDs = trainingDs,
        #     TrainingLBs = trainingLBs,
        #     TestingDs = testingDs,
        #     TestingLBs = testingLBs,
        #     cfm = cfm
        # )



# main function
# arg
arg_regenerate_editing_interval = True
length = 1680.0
width = 1050.0
fileDirs, subNames = getAllFileUserBased([1]) # only extract college data
cfm = ConfusionMatrix(2,[0,1])
# iterate all task
for i_file in range(0, len(fileDirs)):
    subName =  subNames[i_file]
    for DeltaT in [300,500,700,900,1200,1500]:
        # user dependent
        FVs = []
        LBs = []
        for j_file in range(0, len(fileDirs[i_file])):
            dir = fileDirs[i_file][j_file]
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
            #DeltaT = 500

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

            # test module
            #------------------------------------------------------------------
            TestModule = Editting.SentenceEffortModule(
                cursor_ats = ats_cursor,
                cursor_xs = xs_cursor,
                cursor_ys = ys_cursor,
                kb_ats = refine_ats_keypresses,
                kb_info = refine_keypresses_info
            )
            TestModule.Print2Console()
            #------------------------------------------------------------------

            # Extracting features -----------------------------------------------------------------------

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
                editingAtRange=nonEditingModule.nonEditingIntervals,
                editingType=nonEditingModule.nonEditingTypes,
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
            LBs.extend(FAE.lbs)
            LBs.extend(FANE.lbs)
        # to csv

        fvsToArff('C:\\Users\\csjunwang\\Desktop\\EditingResult\\' +subName+'_'+ str(DeltaT) +'_efv.arff', FVs, LBs, '{Deletion, Insertion, nonEditing}', 'edit')
        # cross validation
        # CrossValidation(FVs, LBs, 3, cfm)
        # cfm.print2console()




















