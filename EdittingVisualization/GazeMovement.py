import numpy as np
import Time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from scipy.stats import linregress

def rotatedata(x,y,a):
    cosa=np.cos(a)
    sina=np.sin(a)
    x = x*cosa-y*sina
    y = x*sina+y*cosa
    return x,y


class GazeMovementVisualization(object):
    def __init__(self, gaze_ats, gaze_xs, gaze_ys, editingMoments, windowLength, delta):
        self.gaze_ats = gaze_ats
        self.gaze_xs = gaze_xs
        self.gaze_ys = gaze_ys
        self.editingMoments = editingMoments
        self.windowLength = windowLength
        self.delta = delta
        # generate rts
        self.gaze_rts = Time.Time().generateRelativeTimeListFromAbsolut(self.gaze_ats)
        # slide window front position
        self.WT_index_front = 0
        self.WT_index_back = None
        self.foundIndex_WT = 0
        self.foundIndex_atF = 0

        self.reahEndFlag = False
        # process
        self.process()
        self.plot()

    def process(self):
        self.momentum_rt = [] # holder
        self.momentum_x = [] # holder
        self.momentum_y = []  # holder
        while self.reahEndFlag  == False:
            rt, sum_x_diff, sum_y_diff = self.SlidingMovingWindow() # compute value inside time window
            self.momentum_x.append(sum_x_diff)
            self.momentum_y.append(sum_y_diff)
            self.momentum_rt.append(rt)
        # processing edit moment
        self.process_editMoment()

    def process_editMoment(self):
        # build editing moment rt
        self.editingMoments.insert(0, self.gaze_ats[0])
        self.editingMoments_rt = Time.Time().generateRelativeTimeListFromAbsolut(self.editingMoments)
        self.editingMoments = self.editingMoments[1:len(self.editingMoments)]
        self.editingMoments_rt = self.editingMoments_rt[1:len(self.editingMoments_rt)]

        self.editingIndexs = []
        lastFound = 0
        for rt in self.editingMoments_rt:
            i = Time.Time().findPositionInFloatList(rt, self.momentum_rt)-1
            lastFound = i
            self.editingIndexs.append(i)

    def plot(self):
        graph_x = np.arange(len(self.momentum_rt))
        graph_y1 = np.array(self.momentum_x)
        graph_y2 = np.array(self.momentum_y)

        dfx = pd.DataFrame({'t': graph_x, 'x': graph_y1})
        dfy = pd.DataFrame({'t': graph_x, 'y': graph_y2})

        plt.plot('t', 'x', data=dfx, linestyle='-', marker='.')
        plt.plot('t', 'y', data=dfy, linestyle='-', marker='.')
        plt.legend()

        for edit_index in self.editingIndexs:
            plt.axvline(x=edit_index)
        plt.xlim(200, graph_x[-1])
        plt.show()
        print('d')

    def SlidingMovingWindow(self):
        current_rt_f = self.gaze_rts[self.WT_index_front]
        current_rt_b = current_rt_f + self.windowLength
        # check end
        print(str(current_rt_b)+' '+str(self.gaze_rts[-1]) )
        if current_rt_b >= self.gaze_rts[-1]:

            self.reahEndFlag = True
            current_rt_b = self.gaze_rts[-1]

        self.WT_index_back = Time.Time().findPositionInFloatList(current_rt_b, self.gaze_rts, self.foundIndex_WT)
        if self.WT_index_back > len(self.gaze_rts):
            self.WT_index_back = len(self.gaze_rts)

        self.foundIndex_WT = self.WT_index_back
        # compute movement
        sum_x_diff, sum_y_diff = self.computeGM()
        # update
        at_f = Time.Time().addByNms(self.gaze_ats[self.WT_index_front], self.delta)

        self.WT_index_front = Time.Time().findPositionInTimeArray(at_f, self.gaze_ats, self.foundIndex_atF)-1
        self.foundIndex_atF = self.WT_index_front
        return (current_rt_f+current_rt_b)/2.0, sum_x_diff, sum_y_diff

    # compute movement
    def computeGM(self):
        in_gaze_rts = self.gaze_rts[self.WT_index_front:self.WT_index_back]
        in_gaze_xs = self.gaze_xs[self.WT_index_front:self.WT_index_back]
        in_gaze_ys = self.gaze_ys[self.WT_index_front:self.WT_index_back]
        # compute diff
        x_diffs = np.abs(np.diff(np.array(in_gaze_xs)))
        y_diffs = np.abs(np.diff(np.array(in_gaze_ys)))
        # compute sum of diffs
        sum_x_diff = np.sum(x_diffs)
        sum_y_diff = np.sum(y_diffs)
        return sum_x_diff, sum_y_diff

    # compute features
    def ExtractFeaturesFromGM(self, inRange_xs, inRange_ys):
        inRange_xs_array = np.array(inRange_xs)
        inRange_ys_array = np.array(inRange_ys)
        # compute correlation
        corr_xy = pearsonr(inRange_xs_array, inRange_ys_array)[0]
        # slope
        xs = np.arange(len(inRange_xs))
        slope_x = linregress(xs, inRange_xs_array)[0]
        slope_y = linregress(xs, inRange_ys_array)[0]
        # stair value
        mx,_ = np.polyfit(xs, inRange_xs_array, 1)
        my,_ = np.polyfit(xs, inRange_ys_array, 1)
        _, stair_x_inRange = rotatedata(xs, inRange_xs_array, -np.arctan(mx))
        _, stair_y_inRange = rotatedata(xs, inRange_ys_array, -np.arctan(my))
        # statistic stair
        mean_stair_x_inRange = stair_x_inRange.mean()
        mean_stair_y_inRange = stair_y_inRange.mean()
        min_stair_x_inRange = stair_x_inRange.min()
        min_stair_y_inRange = stair_y_inRange.min()
        max_stair_x_inRange = stair_x_inRange.max()
        max_stair_y_inRange = stair_y_inRange.max()
        f_d = {
            'corri': corr_xy,
            'slope_x': slope_x,
            'slope_y': slope_y,
            'mean_stair_x': mean_stair_x_inRange,
            'mean_stair_y': mean_stair_y_inRange,
            'min_stair_x': min_stair_x_inRange,
            'min_stair_y': min_stair_y_inRange,
            'max_stair_x': max_stair_x_inRange,
            'max_stair_y': max_stair_y_inRange,
        }
        return f_d

class GMFeatureModule(object):

    def __init__(self, gaze_ats, gaze_xs, gaze_ys, windowLength, delta):
        self.gaze_ats = gaze_ats
        self.gaze_xs = gaze_xs
        self.gaze_ys = gaze_ys
        self.windowLength = windowLength
        self.delta = delta
        # generate rts
        self.gaze_rts = Time.Time().generateRelativeTimeListFromAbsolut(self.gaze_ats)
        # slide window front position
        self.WT_index_front = 0
        self.WT_index_back = None
        self.foundIndex_WT = 0
        self.foundIndex_atF = 0
        self.reahEndFlag = False
        # process
        self.process()
        self.fd = self.ExtractFeaturesFromGM(self.momentum_x, self.momentum_y)

    def SlidingMovingWindow(self):
        current_rt_f = self.gaze_rts[self.WT_index_front]
        current_rt_b = current_rt_f + self.windowLength
        # check end
        print(str(current_rt_b)+' '+str(self.gaze_rts[-1]) )
        if current_rt_b >= self.gaze_rts[-1]:

            self.reahEndFlag = True
            current_rt_b = self.gaze_rts[-1]

        self.WT_index_back = Time.Time().findPositionInFloatList(current_rt_b, self.gaze_rts, self.foundIndex_WT)
        if self.WT_index_back > len(self.gaze_rts):
            self.WT_index_back = len(self.gaze_rts)

        self.foundIndex_WT = self.WT_index_back
        # compute movement
        sum_x_diff, sum_y_diff = self.computeGM()
        # update
        at_f = Time.Time().addByNms(self.gaze_ats[self.WT_index_front], self.delta)

        self.WT_index_front = Time.Time().findPositionInTimeArray(at_f, self.gaze_ats, self.foundIndex_atF)-1
        self.foundIndex_atF = self.WT_index_front
        return (current_rt_f+current_rt_b)/2.0, sum_x_diff, sum_y_diff
    # compute movement
    def computeGM(self):
        in_gaze_rts = self.gaze_rts[self.WT_index_front:self.WT_index_back]
        in_gaze_xs = self.gaze_xs[self.WT_index_front:self.WT_index_back]
        in_gaze_ys = self.gaze_ys[self.WT_index_front:self.WT_index_back]
        # compute diff
        x_diffs = np.abs(np.diff(np.array(in_gaze_xs)))
        y_diffs = np.abs(np.diff(np.array(in_gaze_ys)))
        # compute sum of diffs
        sum_x_diff = np.sum(x_diffs)
        sum_y_diff = np.sum(y_diffs)
        return sum_x_diff, sum_y_diff

    def process(self):
        self.momentum_rt = [] # holder
        self.momentum_x = [] # holder
        self.momentum_y = []  # holder
        while self.reahEndFlag  == False:
            rt, sum_x_diff, sum_y_diff = self.SlidingMovingWindow() # compute value inside time window
            self.momentum_x.append(sum_x_diff)
            self.momentum_y.append(sum_y_diff)
            self.momentum_rt.append(rt)

    # compute features
    def ExtractFeaturesFromGM(self, inRange_xs, inRange_ys):
        inRange_xs_array = np.array(inRange_xs)
        inRange_ys_array = np.array(inRange_ys)
        # compute correlation
        corr_xy = pearsonr(inRange_xs_array, inRange_ys_array)[0]
        # slope
        xs = np.arange(len(inRange_xs))
        slope_x = linregress(xs, inRange_xs_array)[0]
        slope_y = linregress(xs, inRange_ys_array)[0]
        # stair value
        mx, _ = np.polyfit(xs, inRange_xs_array, 1)
        my, _ = np.polyfit(xs, inRange_ys_array, 1)
        _, stair_x_inRange = rotatedata(xs, inRange_xs_array, -np.arctan(mx))
        _, stair_y_inRange = rotatedata(xs, inRange_ys_array, -np.arctan(my))
        # statistic stair
        mean_stair_x_inRange = stair_x_inRange.mean()
        mean_stair_y_inRange = stair_y_inRange.mean()
        min_stair_x_inRange = stair_x_inRange.min()
        min_stair_y_inRange = stair_y_inRange.min()
        max_stair_x_inRange = stair_x_inRange.max()
        max_stair_y_inRange = stair_y_inRange.max()
        f_d = {
            'corri': corr_xy,
            'slope_x': slope_x,
            'slope_y': slope_y,
            'mean_stair_x': mean_stair_x_inRange,
            'mean_stair_y': mean_stair_y_inRange,
            'min_stair_x': min_stair_x_inRange,
            'min_stair_y': min_stair_y_inRange,
            'max_stair_x': max_stair_x_inRange,
            'max_stair_y': max_stair_y_inRange,
        }
        return f_d
