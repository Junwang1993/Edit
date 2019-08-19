import cv2
from glob import glob
import numpy as np
import  Time
import CsvReader
import ConvertTimeDomainToVideo
import DataPreprocessing
import Editting
import Visualization
import GetTextArea
from pathlib import Path
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

def getKeyboardInfoInGivenAtInterval(at_interval, ats, info_types, keypressInfo):
    f_at = at_interval[0]
    b_at = at_interval[1]
    # determine the range in keyboard info list
    f_index = Time.Time().findPositionInTimeArray(f_at, ats)-1
    b_index = Time.Time().findPositionInTimeArray(b_at, ats)-1
    # return info
    refine_ats = []
    refine_keypresses = []
    for i in range(f_index, b_index+1):
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
for i_file in range(0, len(fileDirs)):
    print(str(i_file))
    dir = fileDirs[i_file]
    fileNeedToFind = dir+'writingPosition.csv'
    my_file = Path(fileNeedToFind)
    if my_file.is_file():
        continue
    # get csv file
    if len(glob(dir + '*gaze*.csv')) == 0:
        continue
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
    # read keyboard info
    csv4 = CsvReader.CsvReader(glob(dir + '*mouse*.csv')[0])
    data_keyboard = csv4.getData([0, 2, 3], hasHeader=1, needHandleNegativeOneIndex=[], flag=True)
    ats_cursor = [Time.Time(at) for at in data_keyboard[0]]
    info_types = data_keyboard[1]
    keypressInfo = data_keyboard[2]
    # read video
    cap = cv2.VideoCapture(glob(dir + 'window*.avi')[0])
    # setting start point
    cap.set(1, start_v)
    # iterate frames
    # holders
    ats = []
    xs = []
    ys = []
    for i in range(start_v, end_v):
        print('Frame: '+str(i))
        _, frame = cap.read()
        textboxs = GetTextArea.detectPassageArea(frame)
        # append at
        ats.append(at_video[i])
        if textboxs[1] != [0,0,0,0]:
            cv2.circle(frame, (int(textboxs[1][0]), int(15+0.5*(textboxs[1][2]+textboxs[1][3]))), 5, (0, 0, 255), -1)
            xs.append(int(textboxs[1][0]))
            ys.append(int(15+0.5*(textboxs[1][2]+textboxs[1][3])))
        else:
            cv2.circle(frame, (int(textboxs[0][1]), int(0.5 * (textboxs[0][2] + textboxs[0][3]))), 5, (0, 0, 255),-1)
            xs.append(int(textboxs[0][1]))
            ys.append(int(0.5 * (textboxs[0][2] + textboxs[0][3])))
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(100) & 0xFF == ord('q'):
        #     break
    f=open(dir+'writingPosition.csv','w')
    for i_wp in range(0, len(ats)):
        line = Time.Time().toString(ats[i_wp])+','+str(xs[i_wp])+','+str(ys[i_wp])
        f.write(line)
        f.write('\n')
    f.close()
