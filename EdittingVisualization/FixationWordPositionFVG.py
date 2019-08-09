import scipy
import scipy.stats
import cv2
import GetTextArea
import numpy as np

class FixationWordPositionFVG(object):
    @staticmethod
    def computeDistance(frame_f, frame_b, gxs, gys):
        length = 1680.0
        width = 1050.0
        marks_f = [-1,-1]
        marks_b = [-1,-1]
        boxs = GetTextArea.detectTextArea_chinese(frame_f)
        if len(boxs)==0:
            return None
        _, boxs_2d = GetTextArea.sortCoutours(boxs)
        marks_f[0] = boxs_2d[-1][-1][0]+boxs_2d[-1][-1][2]
        marks_f[1] = boxs_2d[-1][-1][1]+(boxs_2d[-1][-1][3]/2.0)
        # #Test
        # cv2.circle(frame_f,(int(marks_f[0]), int(marks_f[1])), 5, (0,255,0), -1)
        # cv2.imshow("dsds",frame_f)
        # #
        boxs = GetTextArea.detectTextArea_chinese(frame_b)
        if len(boxs) == 0:
            return None
        _, boxs_2d = GetTextArea.sortCoutours(boxs)
        marks_b[0] = boxs_2d[-1][-1][0] + boxs_2d[-1][-1][2]
        marks_b[1] = boxs_2d[-1][-1][1] + (boxs_2d[-1][-1][3]/2.0)
        gx = scipy.average(scipy.array(gxs))*length
        gy = scipy.average(scipy.array(gys))*width
        dx = ((marks_f[0] - gx) + (marks_b[0] - gx)) / 2.0
        dy = ((marks_f[1] - gy) + (marks_b[1] - gy)) / 2.0
        if dx>2000:
            print('dsd')
        return [dx, dy]

    @staticmethod
    def computeDistanceV2(frame_f, frame_b, gxs, gys):
        length = 1680.0
        width = 1050.0
        marks_f = [-1, -1]
        marks_b = [-1, -1]
        boxs = GetTextArea.detectTextArea_chinese(frame_f)
        if len(boxs) == 0:
            return None
        _, boxs_2d_f = GetTextArea.sortCoutours(boxs)
        boxs = GetTextArea.detectTextArea_chinese(frame_b)
        if len(boxs) == 0:
            return None
        _, boxs_2d_b = GetTextArea.sortCoutours(boxs)

        gx = scipy.average(scipy.array(gxs)) * length
        gy = scipy.average(scipy.array(gys)) * width

        layout_f = FixationWordPositionFVG.getCurrentLineLayout(boxs_2d_f)
        layout_b = FixationWordPositionFVG.getCurrentLineLayout(boxs_2d_b)
        if len(layout_b) != len(layout_f):
            return None

        layout = FixationWordPositionFVG.avgLayout(layout_f, layout_b)
        dx, dy = FixationWordPositionFVG.getDistance(gx, gy,layout,boxs_2d_f,boxs_2d_b)
        return [dx, dy]

    @staticmethod
    def avgLayout(layout_f, layout_b):
        layout = None
        if len(layout_f) == len(layout_b):
            layout = np.array(layout_f)+np.array(layout_b)
            layout = layout/2.0
            layout = layout.tolist()
        else:
            layout = []
            minLength = min(len(layout_f), len(layout_b))
            is_f_longer = (len(layout_f) > len(layout_b))
            for i in range(0, minLength):
                layout.append((layout_f[i]+layout_b[i])/2.0)
            for i in range(minLength,max(len(layout_f), len(layout_b))):
                if is_f_longer:
                    layout.append(float(layout_f[i]))
                else:
                    layout.append(float(layout_b[i]))
        return layout
    def __init__(self):
        self.dx = []
        self.dy = []
        self.timeLast = []

    def addOneInstance(self, distances, time):
        self.dx.append(distances[0])
        self.dy.append(distances[1])
        self.timeLast.append(time)
    def generateFeatureVector(self, totalFixationTime):
        hist_x, _ = np.histogram(a=np.array(self.dx), bins=15, weights=np.array(self.timeLast), density=False)
        hist_y, _ = np.histogram(a=np.array(self.dy), bins=15, weights=np.array(self.timeLast), density=False)
        hist_x = hist_x/hist_x.max()
        hist_y = hist_y/hist_y.max()
        #
        features = []
        features.append(scipy.stats.skew(hist_x))
        features.append(scipy.stats.skew(hist_y))
        features.append(scipy.stats.kurtosis(hist_x))
        features.append(scipy.stats.kurtosis(hist_y))
        return features

    @staticmethod
    def getCurrentLineLayout(boxs_2d):
        layout = []
        # format [top, bottom]
        for line in boxs_2d:
            all_top = [item[1] for item in line]
            all_height = [item[3] for item in line]
            top = min(all_top)
            all_bottom = np.array(all_top) + np.array(all_height)
            all_bottom = all_bottom.tolist()
            bottom = max(all_bottom)
            mid = float(float(bottom+top)/2)
            layout.append(mid)
        return layout

    @staticmethod
    def getCurrentLineLayoutV2(boxs_2d):
        layout = []
        for line in boxs_2d:
            all_top = [item[1] for item in line]
            all_height = [item[3] for item in line]
            top = min(all_top)
            all_bottom = np.array(all_top) + np.array(all_height)
            all_bottom = all_bottom.tolist()
            bottom = max(all_bottom)
            mid = float(float(bottom+top)/2)
            layout.append(mid)
        # adding top and bottom
        # top
        line_first = boxs_2d[0]
        all_top = [item[1] for item in line_first]
        top = min(all_top)
        all_height = [item[3] for item in line_first]
        height = max(all_height)
        t = (top - (1/2.0)*height)
        # bottom
        line_last = boxs_2d[-1]
        all_top = [item[1] for item in line_last]
        top = min(all_top)
        all_height = [item[3] for item in line_last]
        height = max(all_height)
        b = (top + (3 / 2.0) * height)
        return layout, t, b

    @staticmethod
    def computeAvgLength(layout, boxs_2d):
        # when this function is called, layout is at least 1
        totalLength = 0
        numFullLength = len(layout)-1
        for i in range(0, len(layout)-1):
            lineLingth = boxs_2d[i][-1][0]+boxs_2d[i][-1][2]-boxs_2d[i][0][0]
            totalLength += lineLingth
        return float(totalLength)/numFullLength

    @staticmethod
    def getDistance(gx, gy, layout, boxs_2d_f, boxs_2d_b):
        dx = -1
        dy = -1
        # first determine which line:
        if len(layout) <=1:
            mark_x = (boxs_2d_f[-1][-1][0] + boxs_2d_f[-1][-1][2])/2.0+(boxs_2d_b[-1][-1][0] + boxs_2d_b[-1][-1][2])/2.0
            dx = gx - mark_x
        else:
            avgLength_f = FixationWordPositionFVG.computeAvgLength(layout, boxs_2d_f)
            avgLength_b = FixationWordPositionFVG.computeAvgLength(layout, boxs_2d_b)
            avgLength = (avgLength_f+avgLength_b)/2.0

            # determine which the close one
            middle_clost = min(layout, key=lambda x: abs(x - gy))
            # find index
            line = layout.index(middle_clost)

            # determine whether it is last line
            if line == len(layout)-1:
                dx = gx - (((boxs_2d_f[-1][-1][0] + boxs_2d_f[-1][-1][2])/2.0)+((boxs_2d_b[-1][-1][0] + boxs_2d_b[-1][-1][2])/2.0))
            else:
                # add perious row length
                dx = avgLength*(len(layout)-line)
                d_behind = avgLength - (((boxs_2d_f[-1][-1][0] + boxs_2d_f[-1][-1][2])/2.0)+((boxs_2d_b[-1][-1][0] + boxs_2d_b[-1][-1][2])/2.0)) + (boxs_2d_f[-1][0][0]+boxs_2d_b[-1][0][0])/2.0
                d_front = gx - ((boxs_2d_f[line][0][0]/2.0)+(boxs_2d_b[line][0][0]/2.0))
                dx = -1*(dx- d_behind-d_front)
        mark_y = (boxs_2d_f[-1][-1][1] + (boxs_2d_f[-1][-1][3]/2.0)+ boxs_2d_b[-1][-1][1] + (boxs_2d_b[-1][-1][3]/2.0))/2.0
        dy = mark_y -gy
        return dx, dy






