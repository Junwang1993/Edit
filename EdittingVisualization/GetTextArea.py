import cv2
import numpy as np
from operator import itemgetter, attrgetter
from FixationWordPositionFVG import *
import collections

def isLocationInTextBox(x, y, boxes):
    # find line number first
    _, boxs_2d = GetTextArea.sortCoutours(boxes)
    layout, t, b =  FixationWordPositionFVG.getCurrentLineLayoutV2(boxs_2d)
    # outside?
    if y<t or y>b:
        return False
    else:
        # determine which the close one
        middle_clost = min(layout, key=lambda valueInLayout: abs(valueInLayout - y))
        # check x
        flag = False
        middle_clost_line = layout.index(middle_clost)
        boxes_Line = boxs_2d[middle_clost_line]
        for box in boxes_Line:
            box_x_left = box[0]
            box_x_right = box[0]+box[2]
            if x>=box_x_left and x<=box_x_right:
                flag = True
                break
            if x<box_x_left:
                break
        return flag

def detectTextArea_english(frame):
    boxs = []
    gray = cv2.cvtColor(frame[70:980, :], cv2.COLOR_BGR2GRAY)  # grayscale
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2))
    dilated = cv2.dilate(thresh, kernel, iterations=1)  # dilate
    #cv2.imshow('frame2', dilated)
    _, contours, hierarchy = cv2.findContours(dilated,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) # get contours
    [x_l, x_r, y_t, y_d] = findWordsOptionArea(frame[70:980, :])
    # for each contour found, draw a rectangle around it on original image
    for contour in contours:
        # get rectangle bounding contour
        [x, y, w, h] = cv2.boundingRect(contour)
        # discard areas that are too large
        if h > 300 and w > 300:
            continue
        # discard areas that are too small

        #for Chinese-
        # if h < 20:
        #     continue
        #-----------
        if w < 10:
            continue
        if x>=x_l and x+w<=x_r and y>=y_t and y+h<=y_d:
            continue
        y  = y-4
        h  = h+8
        boxs.append([x, y+70, w, h])
    boxs,_ = sortCoutours(boxs)
    # for  chinese-------------------------
    # boxs = breakLongBoxByEstimation(boxs)
    #--------------------------------------
    return boxs


def detectTextArea_chinese(frame):
    boxs = []
    gray = cv2.cvtColor(frame[100:980, :], cv2.COLOR_BGR2GRAY)  # grayscale
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
    dilated = cv2.dilate(thresh, kernel, iterations=2)  # dilate
    #cv2.imshow('frame2', dilated)
    _, contours, hierarchy = cv2.findContours(dilated,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) # get contours
    [x_l, x_r, y_t, y_d] = findWordsOptionArea(frame[100:980, :])
    # for each contour found, draw a rectangle around it on original image

    for contour in contours:
        # get rectangle bounding contour
        [x, y, w, h] = cv2.boundingRect(contour)
        # discard areas that are too large
        if h > 300 and w > 300:
            continue
        # discard areas that are too small

        #for Chinese-
        if h < 20:
            continue
        #-----------
        if w < 13:
            continue
        if x>=x_l and x+w<=x_r and y>=y_t and y+h<=y_d:
            continue
        y  = y-4
        h  = h+8
        boxs.append([x, y+100, w, h])
    boxs,_ = sortCoutours(boxs)
    # for  chinese-------------------------
    boxs = breakLongBoxByEstimation(boxs)
    #--------------------------------------
    return boxs

def breakLongBoxByEstimation(boxs):
    #
    if len(boxs) == 0:
        return boxs
    all_w = np.array(boxs).T[2]
    all_w.sort()
    length = len(boxs)
    all_w = all_w[int(length*(1.0/4)):int(length*(2.0/4))]
    #estimate_w = np.mean(all_w)
    estimate_w = 23
    # break
    refineBox = []
    for [x,y,w,h] in boxs:
        if w > 40:
            times = int(float(w) / estimate_w)
            for i in range(0, times):
                refineBox.append([int(x+i*estimate_w+2),y,int(estimate_w),h])
        else:
            # no need to break
            refineBox.append([x,y,w,h])
    return refineBox

def refineBoxes(boxs, frame):
    leftLine = 520
    # sort
    sortedBoxes, sortedBoxes_2d = sortCoutours(boxs)
    sortedBoxes_2d_refine = []
    # adding new boxes
    for i in range(0, len(sortedBoxes_2d)):
        sortedBoxes_2d_refine.append([])
        frontRightFlag = leftLine
        for j in range(0, len(sortedBoxes_2d[i])):
            if abs(frontRightFlag - sortedBoxes_2d[i][j][0])<=18:
                # no gap
                sortedBoxes_2d_refine[i].append(sortedBoxes_2d[i][j])
            else:
                # adding
                addingBox = [frontRightFlag+1, sortedBoxes_2d[i][j][1], sortedBoxes_2d[i][j][0]-frontRightFlag-1, sortedBoxes_2d[i][j][3]]
                sortedBoxes_2d_refine[i].insert(j, addingBox)
                sortedBoxes_2d_refine[i].append(sortedBoxes_2d[i][j])
            # update
            frontRightFlag = sortedBoxes_2d[i][j][0]+sortedBoxes_2d[i][j][2]
        # check last box whether need to add
        lastRightLine = 1140
        d = abs(lastRightLine - (sortedBoxes_2d_refine[i][-1][0] + sortedBoxes_2d_refine[i][-1][2]))
        if d > 18:
            # add
            addingBox  = [sortedBoxes_2d_refine[i][-1][0] + sortedBoxes_2d_refine[i][-1][2]+1, sortedBoxes_2d_refine[i][-1][1], d, sortedBoxes_2d_refine[i][-1][3]]
            # check whether there is black color
            part = frame[addingBox[1]:addingBox[1]+addingBox[3], addingBox[0]:addingBox[0]+addingBox[2]]
            #cv2.imshow('part', part)
            part = cv2.cvtColor(part, cv2.COLOR_BGR2GRAY)  # grayscale
            _, part = cv2.threshold(part,127,255,cv2.THRESH_BINARY)
            black = list(part.ravel()).count(0)
            if black > 0:
                sortedBoxes_2d_refine[i].append(addingBox)
    # new part
    sortedBoxes_2d_refine_twice = []
    for i in range(0, len(sortedBoxes_2d_refine)):
        sortedBoxes_2d_refine_twice.append([])
        for j in range(0, len(sortedBoxes_2d_refine[i])):
            box = sortedBoxes_2d_refine[i][j]
            flag, boxes = isStopBox(box, frame)
            if not flag:
                sortedBoxes_2d_refine_twice[-1].append(boxes)
            else:
                for b in boxes:
                    sortedBoxes_2d_refine_twice[-1].append(b)
    #
    sortedBoxes_2d_refine_three = []
    for i in range(0, len(sortedBoxes_2d_refine_twice)):
        sortedBoxes_2d_refine_three.append([])
        for j in range(0, len(sortedBoxes_2d_refine_twice[i])):
            addingBox = sortedBoxes_2d_refine_twice[i][j]
            part = frame[addingBox[1]:addingBox[1] + addingBox[3], addingBox[0]:addingBox[0] + addingBox[2]]
            black = list(part.ravel()).count(0)
            if black > 0:
                sortedBoxes_2d_refine_three[i].append(addingBox)
    sortedBoxes_1d_refine = []
    for i in range(0, len(sortedBoxes_2d_refine_three)):
        for j in range(0, len(sortedBoxes_2d_refine_three[i])):
            sortedBoxes_1d_refine.append(sortedBoxes_2d_refine_three[i][j])

    return sortedBoxes_1d_refine, sortedBoxes_2d_refine_three

def isStopBox(box, frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # grayscale
    _, frame = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
    flag = False
    flags = []
    boxes= []
    #
    x = box[0]
    y = box[1]
    w = box[2]
    h = box[3]
    # check whether it is long box
    boxesNeedToConsider = []
    if w > 40:
        # need to break
        estimate_w = 23
        times = int(float(w) / estimate_w)
        for i in range(0, times):
            boxesNeedToConsider.append([int(x + i * estimate_w + 2), y, int(estimate_w), h])
    # check it is punctuation
    for b in boxesNeedToConsider:
        box_frame = frame[b[1]:b[1]+b[3], b[0]:b[0]+b[2]]
        #cv2.imshow('ddad', box_frame)
        row_box = len(box_frame)
        column_box = len(box_frame[0])
        leftDown = box_frame[int(0.5*row_box):row_box, 0:int(0.5*column_box)]
        black_leftDown = list(leftDown.ravel()).count(0)
        black_else = list(box_frame.ravel()).count(0)-black_leftDown

        ratio_leftDown = black_leftDown / (len(leftDown)*len(leftDown[0]))
        ratio_else = black_else / (row_box * column_box)
        if ratio_leftDown > 0.02 and ratio_else < 0.0041:
            flag = True
            flags.append(True)
        else:
            flags.append(False)
    # make new box new layout
    if flag:
        puncIndexs = np.where(flags)[0]
        for i in range(0, len(puncIndexs)):
            if i == 0:
                puncIndex = puncIndexs[i]
                if puncIndex - 1>=0:
                    w = boxesNeedToConsider[puncIndex-1][0]+boxesNeedToConsider[puncIndex-1][2] -boxesNeedToConsider[0][0]
                    boxes.append([boxesNeedToConsider[0][0],boxesNeedToConsider[0][1],w, boxesNeedToConsider[0][3]])
                boxes.append(boxesNeedToConsider[puncIndex])
            else:
                currentPuncIndex = puncIndexs[i]
                lastPuncIndex = puncIndexs[i-1]
                if currentPuncIndex - lastPuncIndex>1:
                    x = boxesNeedToConsider[lastPuncIndex+1][0]
                    w = boxesNeedToConsider[currentPuncIndex-1][0]+boxesNeedToConsider[currentPuncIndex-1][2]-x
                    y = boxesNeedToConsider[lastPuncIndex+1][1]
                    h = boxesNeedToConsider[lastPuncIndex+1][3]
                    boxes.append([x,y,w,h])
                boxes.append(boxesNeedToConsider[currentPuncIndex])
        # add last part
        if puncIndexs[-1] < len(boxesNeedToConsider)-1:
            lastPuncIndex = puncIndexs[-1]
            x = boxesNeedToConsider[lastPuncIndex+1][0]
            y = boxesNeedToConsider[lastPuncIndex + 1][1]
            h = boxesNeedToConsider[lastPuncIndex + 1][3]
            w = boxesNeedToConsider[-1][0]+boxesNeedToConsider[-1][2] - x
            boxes.append([x,y,w,h])
        return flag, boxes
    else:
        return flag, box

def detectPassageArea(frame):
    [x_l, x_r, y_t, y_d] = [1680, 0, 1050, 0]
    [x_ol, x_or, y_ot, y_od] = [0, 0, 0, 0]
    boxs = detectTextArea_chinese(frame)
    _, boxs_2d = sortCoutours(boxs)
    if len(boxs_2d) == 0:
        return [[0,0,0,0], [0,0,0,0]]
    # update x
    for line in boxs_2d:
        left = line[0]
        right = line[-1]
        if x_l > left[0]:
            x_l = left[0]
        if x_r < right[0]+right[2]:
            x_r = right[0]+right[2]
    # update y
    line_t = boxs_2d[0]
    line_d = boxs_2d[-1]
    for box in line_t:
        if y_t > box[1]:
            y_t = box[1]
    for box in line_d:
        if y_d < box[1] + box[3]:
            y_d = box[1] + box[3]
    if len(boxs_2d)>=2:
        for box in boxs_2d[-2]:
            if y_ot < box[1] + box[3]:
                y_ot = box[1] + box[3]
        for box in boxs_2d[-1]:
            if x_ol < box[0]+box[2]:
                x_ol = box[0]+box[2]
        x_or = x_r
        y_od = y_d
        if [x_ol, x_or, y_ot, y_od] == [1680, 0, 1050, 0]:
            [x_ol, x_or, y_ot, y_od] = [0, 0, 0, 0]
        return [[x_l, x_r, y_t, y_d],[x_ol, x_or, y_ot+30, y_od]]
    else:
        return [[x_l, x_r, y_t, y_d],[0,0,0,0]]

def drawBoxAroundWord(frame, boxs):
    for [x, y, w, h] in boxs:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    return frame

def getBoxAroundWord(boxs):
    textBoxs = [[], [], [], []] # x, y, w, h
    for [x, y, w, h] in boxs:
        textBoxs[0].append(float(x))
        textBoxs[1].append(float(y))
        textBoxs[2].append(float(w))
        textBoxs[3].append(float(h))
    return textBoxs

def sortCoutours(boxs):
    if len(boxs)==0:
        return [],[]
    boxs = sorted(boxs, key=itemgetter(1)) # y
    lines = []
    line = [boxs[0]]
    for i in range(1, len(boxs)):
        if abs(boxs[i][1] - line[0][1])<=15:
            line.append(boxs[i])
        else:
            lines.append(line)
            line = [boxs[i]]
    if len(line)>0:
        lines.append(line)
    sortedLines = []
    for line in lines:
        sortedLines.append(sorted(line, key=itemgetter(0)))
    sortedBox = []
    sortedBox_2d = []
    for line in sortedLines:
        sortedBox_2d.append(line)
        for box in line:
            sortedBox.append(box)

    return sortedBox, sortedBox_2d

def findWordsOptionArea(frame):
    img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # lower mask(red)(0-10)
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    mask0 = cv2.inRange(img_hsv, lower_red, upper_red)
    # upper mask(red)(170-180)
    lower_red = np.array([170, 50, 50])
    upper_red = np.array([180, 255, 255])
    mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
    # # green mask
    # lower_green = np.array([50, 50, 50])
    # upper_green = np.array([180, 255, 255])
    # mask2 = cv2.inRange(img_hsv, lower_green, upper_green)
    # join my masks
    mask = mask0 + mask1
    # set my output img to zero everywhere except my mask
    o = frame.copy()
    redArea = frame.copy()
    redArea[np.where(mask == 0)] = 0
    # convert 2 bw
    redArea = cv2.cvtColor(redArea, cv2.COLOR_RGBA2GRAY)
    redArea = cv2.threshold(redArea, 10, 255, cv2.THRESH_BINARY)[1]
    redArea = cv2.dilate(redArea, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2)), iterations=5)  # dilate
    #cv2.imshow("a", redArea)
    # cv2.imshow("b", frame)
    _, contours, _ = cv2.findContours(redArea, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    [x1, x2, y1, y2] = [1680, 0 , 1050, 0]
    for contour in contours:
        # get rectangle bounding contour
        [x, y, w, h] = cv2.boundingRect(contour)
        if x<x1:
            x1 = x
        if x>x2:
            x2 = x
        if y<y1:
            y1 = y
        if y>y2:
            y2 = y
        if x+w < x1:
            x1 = x+w
        if x+w > x2:
            x2 = x+w
        if y+h < y1:
            y1 = y+h
        if y+h > y2:
            y2 = y+h
    return [x1, x2, y1, y2]

def isWordsOptionAppear(frame):
    img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # lower mask(red)(0-10)
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    mask0 = cv2.inRange(img_hsv, lower_red, upper_red)
    # upper mask(red)(170-180)
    lower_red = np.array([170, 50, 50])
    upper_red = np.array([180, 255, 255])
    mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
    # # green mask
    # lower_green = np.array([50, 50, 50])
    # upper_green = np.array([180, 255, 255])
    # mask2 = cv2.inRange(img_hsv, lower_green, upper_green)
    # join my masks
    mask = mask0 + mask1
    # set my output img to zero everywhere except my mask
    o = frame.copy()
    redArea = frame.copy()
    redArea[np.where(mask == 0)] = 0
    # convert 2 bw
    redArea = cv2.cvtColor(redArea, cv2.COLOR_RGBA2GRAY)
    redArea = cv2.threshold(redArea, 10, 255, cv2.THRESH_BINARY)[1]
    redArea = cv2.dilate(redArea, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2)), iterations=5)  # dilate
    #cv2.imshow("a", redArea)
    # cv2.waitKey(0)
    #cv2.imshow("b", frame)
    _, contours, _ = cv2.findContours(redArea, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    totalArea = 0
    for c in contours:
        area = cv2.contourArea(c)
        totalArea += area
    print(totalArea)
    if totalArea<3000:
        return False
    else:
        return True



# cap = cv2.VideoCapture("C:\\Users\\JW\\Desktop\\window20170607141943.avi")
# while(cap.isOpened()):
#     _, frame = cap.read()
#     if frame is None:
#         break
#     boxs = detectTextArea(frame)
#     frame = drawBoxAroundWord(frame, boxs)
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# cv2.destroyAllWindows()