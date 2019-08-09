import cv2
import numpy as np
from GetTextArea import isWordsOptionAppear
from GetTextArea import findWordsOptionArea
from glob import glob
import CsvReader
import Time
def findTextCursorPosition(cFrame, lFrame):

    # check words option box shown
    flag = isWordsOptionAppear(cFrame[70:-40, 0:-400])
    if flag == True:
        [x1, x2, y1, y2] = findWordsOptionArea(cFrame[0:-40, 0:-400])
        return [x1-4, y1-5]
    else:

        # cv2.imshow('frame', cFrame)
        # cv2.waitKey(0)

        # to gray scale
        cFrame = cv2.cvtColor(cFrame, cv2.COLOR_BGR2GRAY)
        lFrame = cv2.cvtColor(lFrame, cv2.COLOR_BGR2GRAY)
        diffFrame = cv2.absdiff(cFrame, lFrame)

        _,diffFrame = cv2.threshold(diffFrame, 100, 255, cv2.THRESH_BINARY)
        #cv2.imshow('a', diffFrame)
        numWhite = cv2.countNonZero(diffFrame)

        if numWhite<400:
            diffFrame = diffFrame[70:980, :]
            index =  np.where(diffFrame == 255)
            if len(index[0])>0:
                x = ((index[0][0])+(index[0][-1]))/2 +70
                y = ((index[1][0])+(index[1][-1]))/2
                return  [y,x]
            else:
                return  [-1,-1]
        else:
            return [-1,-1]

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

length = 1680.0
width = 1050.0
fileDirs, fileMarks = getAllFile([1]) # only extract college data
# iterate all task
for i_file in range(0, len(fileDirs)):
    print(i_file)
    allAts = []
    xs = []
    ys = []

    dir = fileDirs[i_file]
    file = glob(dir+'*window*.avi')[0]
    csv2 = CsvReader.CsvReader(glob(dir + 'window*.csv')[0])
    data_video = csv2.getData([0, 1], hasHeader=0, needHandleNegativeOneIndex=[], flag=False)
    at_video = [Time.Time(i) for i in data_video[1]]
    cap = cv2.VideoCapture(file)
    #cap.set(1,7500)
    index = 0
    lastTextCursorPosition = [0, 0]
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret != True:
            break

        if index>0:
            print(index)
            tcp = findTextCursorPosition(frame, lastFrame)
            if tcp[0]==-1:
                tcp = lastTextCursorPosition
            else:
                lastTextCursorPosition = tcp
            # cv2.circle(frame, (int(tcp[0]), int(tcp[1])), 5, (255,0,0),-1)
            # cv2.imshow('frame', frame)
            # if cv2.waitKey(50) & 0xFF == ord('q'):
            #     break
            if not(tcp[0]==-1 or tcp[1]==-1):
                allAts.append(at_video[index])
                xs.append(int(tcp[0]))
                ys.append(int(tcp[1]))

        lastFrame = frame
        index = index+1


    f = open(dir + 'newCursorPosition.csv', 'w')
    for i_wp in range(0, len(allAts)):
        line = Time.Time().toString(allAts[i_wp]) + ',' + str(xs[i_wp]) + ',' + str(ys[i_wp])
        f.write(line)
        f.write('\n')
    f.close()

    cap.release()
    cv2.destroyAllWindows()

