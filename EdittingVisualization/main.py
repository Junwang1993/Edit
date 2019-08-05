import cv2
from glob import glob
import numpy as np
import  Time
import CsvReader
import ConvertTimeDomainToVideo
import DataPreprocessing
import Editting
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

def getCursorPosition(at_wanted, ats_cursor, xs_cursor, ys_cursor, length = 1680.0, width = 1050.0):
    # found index need to substract one
    i = Time.Time().findPositionInTimeArray(at_wanted, ats_cursor)-1
    # refine index
    if i <0:
        i = 0
    if i >= len(ats_cursor):
        i = len(ats_cursor)-1
    # cursor position tuple
    cursor_p = (xs_cursor[i], ys_cursor[i])
    return cursor_p




# main function
length = 1680.0
width = 1050.0
fileDirs, fileMarks = getAllFile([1]) # only extract college data
# iterate all task
for i_file in range(0, len(fileDirs)):
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
    csv3 = CsvReader.CsvReader(glob(dir + '*cursor*.csv')[0])
    data_cursor = csv3.getData([0, 1, 2], hasHeader=1, needHandleNegativeOneIndex=[], flag=True)
    ats_cursor = [Time.Time(at) for at in data_cursor[0]]
    xs_cursor = [float(x) for x in data_cursor[1]]
    ys_cursor = [float(y) for y in data_cursor[2]]
    # convert at of cursor to rt of cursor
    # read video
    cap = cv2.VideoCapture(glob(dir + 'window*.avi')[0])
    # setting start point
    cap.set(1, start_v)
    # editting module
    EdittingModule = Editting.EditingModule(ats_cursor, xs_cursor, ys_cursor)
    # get all insertions time window
    allInsertionTMs = EdittingModule.getAllInertionTimeWindow(dt_front=250, dt_back=250)
    # iterate all insertion time window
    lastIndex_video = 0
    for i_itw in range(0, len(allInsertionTMs)):
        TM_at = allInsertionTMs[i_itw]
        #
        video_index_range = (Time.Time().findPositionInTimeArray(TM_at[0], at_video, lastIndex_video),
                             Time.Time().findPositionInTimeArray(TM_at[1], at_video, lastIndex_video))
        lastIndex_video = video_index_range[-1] # update lastfound index








    # iterate cap
    for i_v in range(start_v, end_v + 1):
        _, frame = cap.read()
        # get gaze info
        at_gaze = at_video[i_v]
        x = length * data_gaze_videoTimeDomain[0][i_v - start_v]
        y = width * data_gaze_videoTimeDomain[1][i_v - start_v]
        # get cursor info
        cursor_p_tuple = getCursorPosition(at_gaze, ats_cursor, xs_cursor, ys_cursor)
        # plot gaze
        cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
        # plot cursor
        a = (int(cursor_p_tuple[0]), int(cursor_p_tuple[1]))
        print(str(a))
        cv2.circle(frame, (int(cursor_p_tuple[0]), int(cursor_p_tuple[1])), 10, (0, 255, 0), -1)

        cv2.imshow('frame', frame) # show frame
        # break point
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break








