import cv2
from glob import glob
import numpy as np
import  Time
import CsvReader
import ConvertTimeDomainToVideo
import DataPreprocessing
import Editting
import Visualization
import os
# functions
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


# main function
length = 1680.0
width = 1050.0
fileDirs, fileMarks = getAllFile([1]) # only extract college data
# iterate all task
for i_file in range(7, len(fileDirs)):
    #print(str(i))
    dir = fileDirs[i_file]
    # get csv file
    csv1 = CsvReader.CsvReader(glob(dir + '*gaze*.csv')[0])
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
    full_gaze_at, full_gaze_data = ConvertTimeDomainToVideo.ConvertTimeDomainToVideo().InsertInterpolateListBack(at_video[start_v:end_v],at_gaze,data_gaze_videoTimeDomain,data_gaze[1:len(data_gaze)])

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
    i_cursor_start = Time.Time().findPositionInTimeArray(refine_ats_keypresses[1],ats_cursor)
    ats_cursor = ats_cursor[i_cursor_start:]
    xs_cursor = xs_cursor[i_cursor_start:]
    ys_cursor = ys_cursor[i_cursor_start:]
    # read writing position info
    csv5 = CsvReader.CsvReader(glob(dir+'*writing*.csv')[0])
    data_wp = csv5.getData([0,1,2], hasHeader=0, needHandleNegativeOneIndex=[], flag=True)
    ats_wp = [Time.Time(at) for at in data_wp[0]]
    xs_wp = [float(at) for at in data_wp[1]]
    ys_wp = [float(at) for at in data_wp[2]]
    WPM = Editting.WritingPositionModule(ats_wp,xs_wp,ys_wp)
    CPM = Editting.CursorPositionModule(ats_cursor, xs_cursor, ys_cursor)
    # read video
    cap = cv2.VideoCapture(glob(dir + 'window*.avi')[0])
    # setting start point
    cap.set(1, start_v)
    # editting module
    EdittingModule = Editting.EditingModule(ats_cursor, xs_cursor, ys_cursor,WPM)

    # iterate all insertion time window
    lastIndex_video = 0
    lastIndex_gaze = 0
    for i_itw in range(0, len(EdittingModule.FullEdittingIntervals)):
        TM_at = EdittingModule.FullEdittingIntervals[i_itw]
        type = EdittingModule.editingTypes[i_itw]
        # get video range
        video_index_range = (Time.Time().findPositionInTimeArray(TM_at[0], at_video, lastIndex_video),
                             Time.Time().findPositionInTimeArray(TM_at[1], at_video, lastIndex_video))
        lastIndex_video = video_index_range[-1] # update last found index
        # get gaze range
        gaze_index_range = (Time.Time().findPositionInTimeArray(TM_at[0], full_gaze_at, lastIndex_gaze),
                             Time.Time().findPositionInTimeArray(TM_at[1], full_gaze_at, lastIndex_gaze))
        lastIndex_gaze = gaze_index_range[-1] # update last found index
        # Editing visualization

        if not os.path.exists(dir+'EditVideo//'):
            os.makedirs(dir+'EditVideo//')

        filename = dir+'EditVideo//editing'+str(i_itw)+'_'+str(type)+'.avi'
        Visualization.EditingTimeWindowVisualization(at_video, cap, video_index_range, full_gaze_at, full_gaze_data, gaze_index_range, CPM, filename)
    cap.release()
    cv2.destroyAllWindows()
    break




