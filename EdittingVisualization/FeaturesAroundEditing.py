import Time
import FixationDetection
import numpy as np
import Editting
from scipy import stats
import os.path
import GazeMovement

import matplotlib #everthing works fine, no backend selected yet
matplotlib.use("TkAgg") #backend selected, would still be fine even if Tk wasnt installed.
import matplotlib.pyplot as plt
# helper function
def ConvertATs2RTs(ats):
    rts  = []
    head = ats[0]
    for i in range(0, len(ats)):
        rts.append(Time.Time().substractionBetweenTwoTime(head, ats[i]))
    return rts


def Refined_find_index_in_ATs(at, ats, lastFoundIndex):
    index =Time.Time().findPositionInTimeArray(at,ats, lastFoundIndex)
    if index<0:
        index = 0
    if index>=len(ats)-1:
        index = len(ats)-1
    return index

def fvs2csv(fvs, lbs, fv_names, fn):
    f = open(fn, 'w')
    # print name line
    name_line = ''
    for n in fv_names:
        name_line += n
        name_line += ','
    name_line += 'label'
    f.write(name_line)
    f.write('\n')
    # print
    for i in range(0, len(fvs)):
        fv_line = ''
        fv = fvs[i]
        for j in range(0, len(fv)):
            fv_line += str(fv[j])
            fv_line +=','
        fv_line += lbs[i]
        f.write(fv_line)
        f.write('\n')
    f.close()



class EditingIndex(object):
    # ------f_full--(delta)--f_edit---t---b_edit--(delta)--b_full
    def __init__(self, f_full_gaze=None, f_edit_gaze=None, f_full_kb=None, f_edit_kb=None, b_full_gaze=None, b_edit_gaze=None, b_full_kb=None, b_edit_kb=None, t_gaze=None, t_kb=None):
        self.f_full_gaze = f_full_gaze
        self.f_edit_gaze = f_edit_gaze
        self.f_full_kb = f_full_kb
        self.f_edit_kb = f_edit_kb
        self.b_full_gaze = b_full_gaze
        self.b_edit_gaze = b_edit_gaze
        self.b_full_kb = b_full_kb
        self.b_edit_kb = b_edit_kb
        # start typing
        self.ti_gaze = t_gaze
        self.ti_kb = t_kb

class AheadEditingIndex(object):
    def __init__(self, startIndex_gaze, editingIndex_gaze, startIndex_kb, editingIndex_kb):
        self.startIndex_gaze = startIndex_gaze
        self.editingIndex_gaze = editingIndex_kb
        self.startIndex_kb = startIndex_gaze
        self.editingIndex_kb = editingIndex_kb

class FeaturesNearEditingPointModule(object):
    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, caretATs, caretXs, caretYs, writingPositionATs, writingPositionXs, writingPositionYs, f_delta_at=500, b_delta_at=500):
        # gaze parameters
        self.ats_gaze = ats_gaze
        self.xs_gaze = xs_gaze
        self.ys_gaze = ys_gaze
        # keyboard parameters
        self.ats_kb = ats_kb
        self.keyInfo_kb = keyInfo_kb
        # editing range
        self.editingAtRange = editingAtRange
        # enviorment parameters
        self.caretATs = caretATs
        self.caretXs = caretXs
        self.caretYs = caretYs
        self.writingPositionATs = writingPositionATs
        self.writingPositionXs = writingPositionXs
        self.writingPositionYs = writingPositionYs
        # delta - ms
        self.f_delta_at = f_delta_at
        self.b_delta_at = b_delta_at

    def preprocess_extract_editingRangeIndex(self):
        self.editingIndexRange = []
        # iterate all editing interval
        # iterating parameters
        lastFoundIndex_gaze = 0
        lastFoundIndex_kb = 0
        for i in range(0, len(self.editingAtRange)):
            one_edit_at_range = self.editingAtRange[i]
            # process front and back at
            f_at = Time.Time().substractByNms(one_edit_at_range[0], self.f_delta_at)
            b_at = Time.Time().addByNms(one_edit_at_range[1], self.b_delta_at)
            # find index in gaze and keyboard position
            f_full_gaze = Refined_find_index_in_ATs(f_at, self.ats_gaze, lastFoundIndex_gaze)
            f_edit_gaze = Refined_find_index_in_ATs(one_edit_at_range[0], self.ats_gaze, lastFoundIndex_gaze)
            b_full_gaze = Refined_find_index_in_ATs(b_at, self.ats_gaze, lastFoundIndex_gaze)
            b_edit_gaze = Refined_find_index_in_ATs(one_edit_at_range[1], self.ats_gaze, lastFoundIndex_gaze)

            f_full_kb = Refined_find_index_in_ATs(f_at, self.ats_kb, lastFoundIndex_kb)
            f_edit_kb = Refined_find_index_in_ATs(one_edit_at_range[0], self.ats_kb, lastFoundIndex_kb)
            b_full_kb = Refined_find_index_in_ATs(b_at, self.ats_kb, lastFoundIndex_kb)
            b_edit_kb = Refined_find_index_in_ATs(one_edit_at_range[1], self.ats_kb, lastFoundIndex_kb)
            # start typing moment
            ti_gaze = None
            ti_kb = None
            if not(one_edit_at_range[2] == None):
                ti_gaze = Refined_find_index_in_ATs(one_edit_at_range[2], self.ats_gaze, lastFoundIndex_gaze)
                ti_kb = Refined_find_index_in_ATs(one_edit_at_range[2], self.ats_kb, lastFoundIndex_kb)

            # update
            lastFoundIndex_gaze = f_full_gaze
            lastFoundIndex_kb = f_full_kb
            ei = EditingIndex(
                f_full_gaze= f_full_gaze,
                f_edit_gaze= f_edit_gaze,
                f_full_kb= f_full_kb,
                f_edit_kb= f_edit_kb,
                b_full_gaze=b_full_gaze,
                b_edit_gaze=b_edit_gaze,
                b_full_kb=b_full_kb,
                b_edit_kb=b_edit_kb,
                ti_gaze = ti_gaze,
                ti_kb = ti_kb,
                typing_at_moment = one_edit_at_range[2]
            )
            self.editingIndexRange.append(ei)

    def beforeEditingOrAfter(self, at, TypingAtPoint):
        # 'at' is fixation time point
        # 'TypingAtPoint' is the time moment that a subject start typing in the editing interval
        # Purpose: to determine that fixation is before the typing point or after
        flag = Time.Time().compareTwoTime(at, TypingAtPoint)
        if flag >0:
            # after
            return 'behind'
        else:
            return 'ahead'

    def distanceBetweenCaret(self, fixationP, caretP, word_width = 20, line_height = 100):
        # positive is before the caret
        # negative is after the caret
        dx = caretP[0] - fixationP[0]
        dy = caretP[1] - fixationP[1]
        # determine type of position before/after  distal/near
        type1 = None
        type2 = None
        if dy >= 0.5 * line_height:
            type1 = 'ahead'
            type2 = 'distal'
        elif dy < 0.5 * line_height and dy >= -0.5 * line_height:
            if dx >= 0:
                type1 = 'ahead'
                type2 = 'near'
            else:
                type1 = 'behind'
                type2 = 'near'
        else:
            type1 = 'behind'
            type2 = 'distal'
        return  type1, type2, dx, dy



    def extractFixationFeatures(self,
                                ats_inRange_gaze, xs_inRange_gaze, ys_inRange_gaze,
                                ats_inRange_cursor, xs_inRange_cursor, ys_inRange_cursor,
                                typing_at_moment
                                ):
        # all features --- dict
        self.fixation_fvl = {
            # fixation features go here!
            'allFixationDur': [],
            'aheadMomemtFixationDur': [],
            'behindMomentFixationDur':[],
            'aheadCaretFixationDur':[],
            'behindCaretFixationDur':[],
            'distalFixationDur':[],
            'nearFixationDur': [],
        }
        # build rts
        rts_inRange_gaze = ConvertATs2RTs(ats_inRange_gaze)
        # detect fixation
        _, _, EfixTuple_index = FixationDetection.fixation_IDT_V2(xs_inRange_gaze, ys_inRange_gaze, rts_inRange_gaze)

        # iterate all fixations
        for i in range(0, len(EfixTuple_index)):
            # one fixation
            f_f_i = EfixTuple_index[i][0]
            f_b_i = EfixTuple_index[i][1]+1
            fixation_at = ats_inRange_gaze[f_f_i]
            fixation_x = np.array(xs_inRange_gaze[f_f_i:f_b_i]).mean()
            fixation_y = np.array(ys_inRange_gaze[f_f_i:f_b_i]).mean()
            # get current caret position
            caretP = Editting.getCursorPosition(fixation_at, self.caretATs, self.caretXs, self.caretYs)
            # fixation duration -- overall
            f_dur = rts_inRange_gaze[f_b_i] - rts_inRange_gaze[f_f_i]
            self.fixation_fvl['allFixationDur'].append(f_dur)
            # determine fixation ---time position---
            time_position_type = self.beforeEditingOrAfter(fixation_at, typing_at_moment)
            # determine fixation ---local position---
            relativeP_type, distance_type, dx2caret, dy2caret = self.distanceBetweenCaret((fixation_x, fixation_y), caretP)
            # determine fixation type
            if time_position_type == 'ahead':
                # ahead moment
                self.fixation_fvl['aheadMomemtFixationDur'].append(f_dur)
            else:
                # behind moment
                self.fixation_fvl['behindMomentFixationDur'].append(f_dur)

            if relativeP_type == 'ahead':
                self.fixation_fvl['aheadCaretFixationDur'].append(f_dur)
            else:
                self.fixation_fvl['behindCaretFixationDur'].append(f_dur)

            if distance_type == 'distal':
                self.fixation_fvl['distalFixationDur'].append(f_dur)
            else:
                self.fixation_fvl['nearFixationDur'].append(f_dur)

    def extract_num_type_fixation(self):

        self.num_type_fvl = {
            'num_fixation': len(self.fixation_fvl['allFixationDur']),
            'num_aheadMoment': len(self.fixation_fvl['aheadMomemtFixationDur']),
            'num_behindMoment': len(self.fixation_fvl['behindMomentFixationDur']),
            'num_aheadCaret': len(self.fixation_fvl['aheadCaretFixationDur']),
            'num_behindCaret': len(self.fixation_fvl['behindCaretFixationDur']),
            'num_near': len(self.fixation_fvl['nearFixationDur']),
            'num_distal': len(self.fixation_fvl['distalFixationDur'])
        }

class FeaturesAheadEditingPointModule(object):

    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, editingType,caretATs, caretXs, caretYs, writingPositionATs, writingPositionXs, writingPositionYs, non = False, deltaT = 1500):
        # gaze
        self.ats_gaze = ats_gaze
        self.xs_gaze = xs_gaze
        self.ys_gaze = ys_gaze
        # keyboard
        self.ats_kb = ats_kb
        self.keyInfo_kb = keyInfo_kb
        # editing
        self.editingAtRange = editingAtRange
        self.editingType = editingType
        # caret
        self.caretATs = caretATs
        self.caretXs = caretXs
        self.caretYs = caretYs
        # writing position
        self.writingPositionATs = writingPositionATs
        self.writingPositionXs = writingPositionXs
        self.writingPositionYs = writingPositionYs

        # delta
        self.deltaT = deltaT
        # preprocessing
        if non == False:
            self.preprocess_extract_editingRangeIndex()
        else:
            self.preprocess_extract_nonEditingRangeIndex()
        self.preprocess_compute_textGeneratedSpeed()
        self.process()

    def reject_outliers(self, data, m=2):
        return data[abs(data - np.mean(data)) < m * np.std(data)]

    def process(self):
        self.fvs = []
        self.lbs = []
        for i in range(0, len(self.editingIndexRange)):
            ei = self.editingIndexRange[i]
            # extracting fixation features
            d_i = ei.b_full_gaze - ei.f_full_gaze
            print(str(d_i))
            if d_i <5:
                continue

            self.extractFixationFeaturesList(
                ats_inRange_gaze = self.ats_gaze[ei.f_full_gaze:ei.b_full_gaze],
                xs_inRange_gaze = self.xs_gaze[ei.f_full_gaze:ei.b_full_gaze],
                ys_inRange_gaze = self.ys_gaze[ei.f_full_gaze:ei.b_full_gaze],
                ats_inRange_cursor = self.caretATs[ei.f_full_gaze:ei.b_full_gaze],
                xs_inRange_cursor = self.caretXs[ei.f_full_gaze:ei.b_full_gaze],
                ys_inRange_cursor = self.caretYs[ei.f_full_gaze:ei.b_full_gaze],
                type = self.editingType[i]
            )
            self.extractTextFeaturesList(
                ats_inRange_kb = self.ats_kb[ei.f_full_kb : ei.b_full_kb],
                info_inRange_kb = self.keyInfo_kb[ei.f_full_kb : ei.b_full_kb],
                full_at_kb = self.ats_kb,
                full_Info_kb = self.keyInfo_kb,
                start_check_reverse = ei.b_full_kb
            )
            self.extractKeyboardDynamicFeaturesList(
                ats_inRange_kb=self.ats_kb[ei.f_full_kb: ei.b_full_kb],
                info_inRange_kb=self.keyInfo_kb[ei.f_full_kb: ei.b_full_kb],
                full_at_kb=self.ats_kb,
                full_Info_kb=self.keyInfo_kb,
                f_index_kb = ei.f_full_kb,
                b_index_kb = ei.b_full_kb
            )

            self.extractGMFeaturesList(
                ats_inRange_gaze = self.ats_gaze[ei.f_full_gaze:ei.b_full_gaze],
                xs_inRange_gaze = self.xs_gaze[ei.f_full_gaze:ei.b_full_gaze],
                ys_inRange_gaze = self.ys_gaze[ei.f_full_gaze:ei.b_full_gaze]
            )

            fv = []
            self.fv_name = []

            # fixation
            fv_fix, fv_name_fix = self.extractFixationFeaturesVector()
            # text
            fv_text, fv_name_text = self.extractTextFeaturesVector()
            # keyboard
            fv_kbd, fv_name_kbd = self.extractKBDFeaturesVector()
            #gm
            fv_gm, fv_name_gm = self.extractGMFeaturesVector()
            # extend
            fv.extend(fv_fix)
            fv.extend(fv_text)
            fv.extend(fv_kbd)
            fv.extend(fv_gm)
            self.fv_name.extend(fv_name_fix)
            self.fv_name.extend(fv_name_text)
            self.fv_name.extend(fv_name_kbd)
            self.fv_name.extend(fv_name_gm)
            # append 2 fvs
            self.fvs.append(fv)
            self.lbs.append(self.editingType[i])

    def distanceBetweenCaret(self, fixationP, caretP, word_width = 20, line_height = 100):
        # positive is before the caret
        # negative is after the caret
        dx = caretP[0] - fixationP[0]
        dy = caretP[1] - fixationP[1]
        # determine type of position before/after  distal/near
        type1 = None
        type2 = None
        if dy >= 0.5 * line_height:
            type1 = 'ahead'
            type2 = 'distal'
        elif dy < 0.5 * line_height and dy >= -0.5 * line_height:
            if dx >= 0:
                type1 = 'ahead'
                type2 = 'near'
            else:
                type1 = 'behind'
                type2 = 'near'
        else:
            type1 = 'behind'
            type2 = 'distal'
        return  type1, type2, dx, dy

    def preprocess_compute_textGeneratedSpeed(self):
        # compute avg KPI
        self.intervalKPIIndexs = []
        self.allKPIIntervals = []
        for i in range(1, len(self.keyInfo_kb)):
            self.intervalKPIIndexs.append(i)
            self.allKPIIntervals.append(Time.Time().substractionBetweenTwoTime(self.ats_kb[i - 1], self.ats_kb[i]))
        kpis = np.array(self.allKPIIntervals)
        kpis_refine = self.reject_outliers(kpis, 2)
        self.avg_kpi = kpis.mean()
        self.std_kpi = kpis.std()

    def preprocess_extract_nonEditingRangeIndex(self):
        self.editingIndexRange = []
        self.editingIndexRanges_for_generating_noEditing = []
        # iterate all editing interval
        # iterating parameters

        for i in range(0, len(self.editingAtRange)):
            lastFoundIndex_gaze = 0
            lastFoundIndex_kb = 0
            one_edit_at_range = self.editingAtRange[i]

            # feature extract range
            at_f = one_edit_at_range[0]
            at_b = one_edit_at_range[1]
            # find gaze index
            f_full_gaze = Refined_find_index_in_ATs(at_f, self.ats_gaze, lastFoundIndex_gaze)
            lastFoundIndex_gaze = f_full_gaze
            b_full_gaze = Refined_find_index_in_ATs(at_b, self.ats_gaze, lastFoundIndex_gaze)

            # find keyboard index
            f_full_kb = Refined_find_index_in_ATs(at_f, self.ats_kb, lastFoundIndex_kb)
            lastFoundIndex_kb = f_full_kb
            b_full_kb = Refined_find_index_in_ATs(at_b, self.ats_kb, lastFoundIndex_kb)

            ei = EditingIndex(
                f_full_gaze=f_full_gaze,
                f_full_kb=f_full_kb,
                b_full_gaze=b_full_gaze,
                b_full_kb=b_full_kb
            )
            self.editingIndexRange.append(ei)
            self.editingIndexRanges_for_generating_noEditing.append((at_f, at_b))

    def preprocess_extract_editingRangeIndex(self):
        self.editingIndexRange = []
        self.editingIndexRanges_for_generating_noEditing = []
        # iterate all editing interval
        # iterating parameters
        lastFoundIndex_gaze = 0
        lastFoundIndex_kb = 0
        for i in range(0, len(self.editingAtRange)):
            one_edit_at_range = self.editingAtRange[i]
            editing_at_moment = one_edit_at_range[0] # at moment that start editing (start moving back)
            # feature extract range
            at_f = Time.Time().substractByNms(editing_at_moment, self.deltaT)
            at_b = editing_at_moment
            # find gaze index
            f_full_gaze = Refined_find_index_in_ATs(at_f, self.ats_gaze, lastFoundIndex_gaze)
            b_full_gaze = Refined_find_index_in_ATs(at_b, self.ats_gaze, lastFoundIndex_gaze)
            lastFoundIndex_gaze = f_full_gaze
            # find keyboard index
            f_full_kb = Refined_find_index_in_ATs(at_f, self.ats_kb, lastFoundIndex_kb)
            b_full_kb = Refined_find_index_in_ATs(at_b, self.ats_kb, lastFoundIndex_kb)
            lastFoundIndex_kb = f_full_kb
            ei = EditingIndex(
                f_full_gaze=f_full_gaze,
                f_full_kb=f_full_kb,
                b_full_gaze=b_full_gaze,
                b_full_kb=b_full_kb
            )
            self.editingIndexRange.append(ei)
            self.editingIndexRanges_for_generating_noEditing.append((at_f, at_b))

    def checkIsStopCharacters(self, full_info_kb, checkIndex):
        # capture all the stop characters
        stop_characters = {
            '<',  # ,
            '</?>',  # ?
            '<.>>',  # .
        }
        half_stop_characters = {
            '1'  # !
        }
        checkC =  full_info_kb[checkIndex]
        if checkC in stop_characters:
            return True
        elif checkC in half_stop_characters:
            # check one character before
            if checkIndex == 0:
                return False
            if full_info_kb[checkIndex-1] == '<LSHIFT>' or full_info_kb[checkIndex-1] == '<RSHIFT>':
                return True
        else:
            return False

    def extractKeyboardDynamicFeaturesList(self, ats_inRange_kb, info_inRange_kb, full_at_kb, full_Info_kb, f_index_kb, b_index_kb):
        # just for initialization
        self.typing_fvl = {
            'kpis_ratio_mean': None,
            'kpis_ratio_std': None,
            'kpis_ratio_max': None,
            'kpis_ratio_min': None
        }
        kpis_interval = []
        for i in range(f_index_kb, b_index_kb):
            kpis_interval.append(self.allKPIIntervals[i])
        kpis_interval_ratio = np.array(kpis_interval)/float(self.avg_kpi)
        kpis_interval_ratio = kpis_interval_ratio.tolist()
        if len(kpis_interval_ratio) ==0:
            self.typing_fvl['kpis_ratio_mean'] = -1
            self.typing_fvl['kpis_ratio_std'] = -1
            self.typing_fvl['kpis_ratio_max'] = -1
            self.typing_fvl['kpis_ratio_min'] = -1
        else:
            self.typing_fvl['kpis_ratio_mean'] = np.array(kpis_interval_ratio).mean()
            self.typing_fvl['kpis_ratio_std'] = np.array(kpis_interval_ratio).std()
            self.typing_fvl['kpis_ratio_max'] = np.max(np.array(kpis_interval_ratio))
            self.typing_fvl['kpis_ratio_min'] = np.min(np.array(kpis_interval_ratio))

    def extractKBDFeaturesVector(self):
        fv = []
        fv_name = []
        for fvn in self.typing_fvl:
            fv_name.append(fvn)
            fv.append(self.typing_fvl[fvn])
        return fv, fv_name

    def extractTextFeaturesList(self, ats_inRange_kb, info_inRange_kb, full_at_kb, full_Info_kb, start_check_reverse):
        # just for initialization
        self.kb_fv = {
            'num_keystrokes' : None,
            'close_stop_character' : None,
            'close_stop_time': None,
            # todo
            'current_box_start_interval': None,
            'avg_kpi_current_box':None,
            'last_delete_time':None
        }


        # number keystrokes
        self.kb_fv['num_keystrokes'] = len(info_inRange_kb)
        # close stop character
        found_closest_stop = False
        numCheck = 0
        reverse_i = start_check_reverse
        while reverse_i >=0:
            #if full_Info_kb[reverse_i] in stop_characters:
            if self.checkIsStopCharacters(full_Info_kb, reverse_i):
                self.kb_fv['close_stop_character'] = numCheck
                found_closest_stop = True
                break
            numCheck += 1
            reverse_i -= 1
        if found_closest_stop == False:
            self.kb_fv['close_stop_character'] = -1
        else:
            # close stop time
            self.kb_fv['close_stop_time'] = Time.Time().substractionBetweenTwoTime(
                full_at_kb[reverse_i],
                full_at_kb[start_check_reverse]
            )

        # refine
        for name in self.kb_fv:
            if self.kb_fv[name] == None:
                self.kb_fv[name] = -1

    def extractTextFeaturesVector(self):
        fv = []
        fv_name = []
        for fvn in self.kb_fv:
            fv_name.append(fvn)
            fv.append(self.kb_fv[fvn])
        return fv, fv_name

    def extractFixationFeaturesList(self, ats_inRange_gaze, xs_inRange_gaze, ys_inRange_gaze,
                                ats_inRange_cursor, xs_inRange_cursor, ys_inRange_cursor, type):
        # initial holder
        self.fixation_fvl = {
            'allFixationDur': [],
            'allFixationPositionType1':[], # ahead or behind
            'allFixationPositionType2':[],
            'd2c_x': [],
            'd2c_y': [],
            'num_fix':[]
        }
        # build rts
        rts_inRange_gaze = ConvertATs2RTs(ats_inRange_gaze)
        # detect fixation
        _, _, EfixTuple_index = FixationDetection.fixation_IDT_V2(xs_inRange_gaze, ys_inRange_gaze, rts_inRange_gaze)
        # iterate all fixations
        for i in range(0, len(EfixTuple_index)):
            # one fixation
            self.fixation_fvl['num_fix'].append(len(EfixTuple_index))
            f_f_i = EfixTuple_index[i][0]
            f_b_i = EfixTuple_index[i][1] + 1
            fixation_at = ats_inRange_gaze[f_f_i]
            fixation_x = np.array(xs_inRange_gaze[f_f_i:f_b_i]).mean()
            fixation_y = np.array(ys_inRange_gaze[f_f_i:f_b_i]).mean()
            # get current caret position
            caretP = Editting.getCursorPosition(fixation_at, self.caretATs, self.caretXs, self.caretYs)
            # fixation duration
            if f_b_i >= len(rts_inRange_gaze):
                f_b_i = len(rts_inRange_gaze)-1
            f_dur = rts_inRange_gaze[f_b_i] - rts_inRange_gaze[f_f_i]
            # determine fixation ---local position---
            relativeP_type, distance_type, dx2caret, dy2caret = self.distanceBetweenCaret((fixation_x, fixation_y), caretP)
            self.fixation_fvl['allFixationDur'].append(f_dur)
            self.fixation_fvl['d2c_x'].append(dx2caret)
            self.fixation_fvl['d2c_y'].append(dy2caret)
            self.fixation_fvl['allFixationPositionType1'].append(relativeP_type)
            self.fixation_fvl['allFixationPositionType2'].append(distance_type)
        return self.fixation_fvl

    def extractFixationFeaturesVector(self):
        # extracting features from features list
        fv_names = []
        fv = []
        fv_names.append('mean_num')
        if len(self.fixation_fvl['num_fix']) != 0:
            fv.append(np.array(self.fixation_fvl['num_fix']).mean())
        else:
            fv.append(0)
        fv_names.append('std_num')
        if len(self.fixation_fvl['num_fix']) != 0:
            fv.append(np.array(self.fixation_fvl['num_fix']).std())
        else:
            fv.append(0)
        fv_names.append('85_num')
        if len(self.fixation_fvl['num_fix']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['num_fix']),85))
        else:
            fv.append(0)
        fv_names.append('15_num')
        if len(self.fixation_fvl['num_fix']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['num_fix']),15))
        else:
            fv.append(0)



        # dur related features
        fv_names.append('dur_mean')
        if len(self.fixation_fvl['allFixationDur'])!=0:
            fv.append(np.array(self.fixation_fvl['allFixationDur']).mean())
        else:
            fv.append(0)

        fv_names.append('dur_std')
        if len(self.fixation_fvl['allFixationDur']) != 0:
            fv.append(np.array(self.fixation_fvl['allFixationDur']).std())
        else:
            fv.append(0)

        fv_names.append('dur_85')
        if len(self.fixation_fvl['allFixationDur']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['allFixationDur']), 85))
        else:
            fv.append(0)

        fv_names.append('dur_15')
        if len(self.fixation_fvl['allFixationDur']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['allFixationDur']), 15))
        else:
            fv.append(0)

        # distance-x
        fv_names.append('dist_x_mean')
        if len(self.fixation_fvl['d2c_x']) != 0:
            fv.append(np.array(self.fixation_fvl['d2c_x']).mean())
        else:
            fv.append(0)

        fv_names.append('dist_x_std')
        if len(self.fixation_fvl['d2c_x']) != 0:
            fv.append(np.array(self.fixation_fvl['d2c_x']).std())
        else:
            fv.append(0)

        fv_names.append('dist_x_85')
        if len(self.fixation_fvl['d2c_x']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['d2c_x']), 85))
        else:
            fv.append(0)

        fv_names.append('dist_x_15')
        if len(self.fixation_fvl['d2c_x']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['d2c_x']), 15))
        else:
            fv.append(0)

        # distance-y
        fv_names.append('dist_y_mean')
        if len(self.fixation_fvl['d2c_y']) != 0:
            fv.append(np.array(self.fixation_fvl['d2c_y']).mean())
        else:
            fv.append(0)

        fv_names.append('dist_y_std')
        if len(self.fixation_fvl['d2c_y']) != 0:
            fv.append(np.array(self.fixation_fvl['d2c_y']).std())
        else:
            fv.append(0)

        fv_names.append('dist_y_85')
        if len(self.fixation_fvl['d2c_y']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['d2c_y']), 85))
        else:
            fv.append(0)

        fv_names.append('dist_y_15')
        if len(self.fixation_fvl['d2c_y']) != 0:
            fv.append(np.percentile(np.array(self.fixation_fvl['d2c_y']), 15))
        else:
            fv.append(0)

        # type 1 ratio
        fv_names.append('behind_ratio')
        if len(self.fixation_fvl['allFixationPositionType1']) != 0:
            fv.append(float(self.fixation_fvl['allFixationPositionType1'].count('behind'))/float(len(self.fixation_fvl['allFixationPositionType1'])))
        else:
            fv.append(0)

        # type 2 ratio
        fv_names.append('distal_ratio')
        if len(self.fixation_fvl['allFixationPositionType2']) != 0:
            fv.append(float(self.fixation_fvl['allFixationPositionType2'].count('distal'))/float(len(self.fixation_fvl['allFixationPositionType2'])))
        else:
            fv.append(0)
        return fv, fv_names

    def extractGMFeaturesList(self, ats_inRange_gaze, xs_inRange_gaze, ys_inRange_gaze):
        GMM = GazeMovement.GMFeatureModule(
            gaze_ats = ats_inRange_gaze,
            gaze_xs = xs_inRange_gaze,
            gaze_ys = ys_inRange_gaze,
            windowLength = 500,
            delta = 500/5.0
        )
        self.gm_fl = GMM.fd

    def extractGMFeaturesVector(self):
        fv = []
        fv_name = []
        for fvn in self.gm_fl:
            fv_name.append(fvn)
            fv.append(self.gm_fl[fvn])
        return fv, fv_name


class Trajectory(object):

    def __init__(self, relative_rts, relative_xs, relative_ys, original = 500 ,ratio= 0.25):
        self.disPlace = float(original)*ratio

        # relative rts => 0 is the time point start editing
        # relatice ps => (0, 0) is the cusor point
        self.relative_rts = relative_rts
        self.relative_xs = relative_xs
        self.relative_ys = relative_ys
        # change ratio
        self.relative_xs = np.array(self.relative_xs)*ratio
        self.relative_ys = np.array(self.relative_ys)*ratio
        self.relative_xs = self.relative_xs.tolist()
        self.relative_ys = self.relative_ys.tolist()
        # caret place
        self.caretP = (0, 0)


    def draw(self, edit_type, filename):
        g_start = 176.0
        b_start = 176.0
        g_end = 0.0
        b_end = 0.0
        # num gaze point
        num_gaze_point = len(self.relative_rts)
        unit_change = abs(g_end-g_start)/float(num_gaze_point)
        # create plot
        fig = plt.figure()
        fig.suptitle(edit_type, fontsize=14, fontweight='bold')
        ax = fig.add_subplot(111)
        ax.scatter([self.caretP[0]],[self.caretP[0]],color='darkgreen',marker = '^')
        for i in range(1, num_gaze_point):
            color_tuple = (1.0, max(0, (g_start-i*unit_change)/255.0), max((b_start-i*unit_change)/255.0,0)) # RGB
            plt.plot([self.relative_xs[i-1], self.relative_xs[i]], [self.relative_ys[i-1], self.relative_ys[i]], color=color_tuple, marker='o',)
        ax.set_xlim(-1*self.disPlace, self.disPlace)
        ax.set_ylim(self.disPlace, -1*self.disPlace)
        plt.savefig(filename)
        plt.close(fig)
        plt.close('all')

class GazeTrajectoryAheadEditingPoint(object):


    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, editingType,caretATs, caretXs, caretYs, writingPositionATs, writingPositionXs, writingPositionYs, box_shown_ats, extraction_type, deltaT = 3000):
        # gaze
        self.ats_gaze = ats_gaze
        self.xs_gaze = xs_gaze
        self.ys_gaze = ys_gaze
        # keyboard
        self.ats_kb = ats_kb
        self.keyInfo_kb = keyInfo_kb
        # editing
        self.editingAtRange = editingAtRange
        self.editingType = editingType
        # caret
        self.caretATs = caretATs
        self.caretXs = caretXs
        self.caretYs = caretYs
        # writing position
        self.writingPositionATs = writingPositionATs
        self.writingPositionXs = writingPositionXs
        self.writingPositionYs = writingPositionYs
        # box_notshown_time
        self.box_shown_ats = box_shown_ats
        # extraction type
        self.extration_type = extraction_type
        # delta
        self.deltaT = deltaT

        self.preprocess_extract_editingRangeIndex()
        self.fetchGazeTrajectory()



    def plotTrajs(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        for i in range(0, len(self.trajs)):
            traj = self.trajs[i]
            label = self.editingType[i]
            traj.draw(label, dir+str(i)+'.png')

    def interpolate_position_version(self, at_want, ats, xs, ys, lastFound = 0):
        idx = Time.Time().findPositionInTimeArray(at_want, ats)
        lastFound = idx
        if idx == 0:
            return (xs[0], ys[0])
        if idx >= len(ats):
            return (xs[-1], ys[-1])
        r_diff = Time.Time().substractionBetweenTwoTime(ats[idx-1], at_want)
        f_diff = Time.Time().substractionBetweenTwoTime(ats[idx-1], ats[idx])
        x = xs[idx-1]+r_diff*((xs[idx]-xs[idx-1])/float(f_diff))
        y = ys[idx-1]+r_diff*((ys[idx]-ys[idx-1])/float(f_diff))
        return (x,y), lastFound

    def getCaretPsAlongGazeAxis(self,caret_ats, caret_xs, caret_ys, gaze_ats, lastFound = 0):
        caret_xs_along_gaze_axis = []
        caret_ys_along_gaze_axis = []

        for i in range(0, len(gaze_ats)):
            g_at = gaze_ats[i]
            p, lastFound = self.interpolate_position_version(g_at, caret_ats, caret_xs, caret_ys, lastFound)
            caret_xs_along_gaze_axis.append(p[0])
            caret_ys_along_gaze_axis.append(p[1])
        return caret_xs_along_gaze_axis, caret_ys_along_gaze_axis, lastFound

    def find_F_edit_interval(self, at_startCheck, lastFound = 0):
        index = Time.Time().findPositionInTimeArray(at_startCheck, self.box_shown_ats)-1
        lastFound = index
        if index < 0:
            index = 0
        if index >= len(self.box_shown_ats)-1:
            index = len(self.box_shown_ats)-1
        return self.box_shown_ats[index], lastFound



    def preprocess_extract_editingRangeIndex(self):
        self.editingIndexRange = []
        # iterate all editing interval
        # iterating parameters
        lastFoundIndex_gaze = 0
        lastFoundIndex_kb = 0
        lastFoundIndex_box = 0
        for i in range(0, len(self.editingAtRange)):
            one_edit_at_range = self.editingAtRange[i]
            editing_at_moment = one_edit_at_range[0] # at moment that start editing (start moving back)
            # feature extract range
            if self.extration_type == 0:
                at_f = Time.Time().substractByNms(editing_at_moment, self.deltaT)
            else:
                at_f, lastFoundIndex_box = self.find_F_edit_interval(editing_at_moment,lastFoundIndex_box)
            at_b = editing_at_moment
            # find gaze index
            f_full_gaze = Refined_find_index_in_ATs(at_f, self.ats_gaze, lastFoundIndex_gaze)
            b_full_gaze = Refined_find_index_in_ATs(at_b, self.ats_gaze, lastFoundIndex_gaze)
            lastFoundIndex_gaze = f_full_gaze
            # find keyboard index
            f_full_kb = Refined_find_index_in_ATs(at_f, self.ats_kb, lastFoundIndex_kb)
            b_full_kb = Refined_find_index_in_ATs(at_b, self.ats_kb, lastFoundIndex_kb)
            lastFoundIndex_kb = f_full_kb
            ei = EditingIndex(
                f_full_gaze=f_full_gaze,
                f_full_kb=f_full_kb,
                b_full_gaze=b_full_gaze,
                b_full_kb=b_full_kb
            )
            self.editingIndexRange.append(ei)

    def fetchGazeTrajectory(self):
        self.trajs = []
        # iterate each ei
        lastFound = 0
        for i in range(0, len(self.editingIndexRange)):
            print(i)
            ei = self.editingIndexRange[i]
            ei_ats_gaze = self.ats_gaze[ei.f_full_gaze:ei.b_full_gaze]
            ei_xs_gaze = self.xs_gaze[ei.f_full_gaze:ei.b_full_gaze]
            ei_ys_gaze = self.ys_gaze[ei.f_full_gaze:ei.b_full_gaze]
            # build relative rts
            ei_rts = Time.Time().generateRelativeTimeListFromAbsolut(ei_ats_gaze)
            ei_rrts = np.array(ei_rts)-ei_rts[-1]
            # from np data format to list
            ei_rrts = ei_rrts.tolist()
            caret_xs, caret_ys, lastFound = self.getCaretPsAlongGazeAxis(self.caretATs, self.caretXs, self.caretYs, ei_ats_gaze)
            relative_xs = (np.array(ei_xs_gaze) - np.array(caret_xs)).tolist()
            relative_ys = (np.array(ei_ys_gaze) - np.array(caret_ys)).tolist()
            traj = Trajectory(ei_rrts, relative_xs, relative_ys)
            self.trajs.append(traj)

class StatisticalOverallOfEditing(object):

    def __init__(self):
        # create some inner parameter
        # capture num
        self.totalNum_Editing = 0
        self.totalNum_Insertion = 0
        self.totalNum_Deletion = 0
        # feature-insertion
        self.insertion_features = {
            'avg_dur': [],  'std_dur':[],
            'avg_dx': [],   'std_dx':[],
            'avg_dy': [],   'std_dy':[],
            'ratio_distal':[],
            'ratio_ahead':[]
        }
        # feature-deletion
        self.deletion_features = {
            'avg_dur': [], 'std_dur': [],
            'avg_dx': [], 'std_dx': [],
            'avg_dy': [], 'std_dy': [],
            'ratio_distal': [],
            'ratio_ahead': []
        }

    def addingEditingInstance(self, edit_type, fd):
        self.totalNum_Editing += 1
        # fd is the feature dict that is in the same form of inner-parameter
        if edit_type == 'Insertion':
            self.totalNum_Insertion += 1
            for fn in fd:
                self.insertion_features[fn].append(fd[fn])
        else:
            self.totalNum_Deletion += 1
            for fn in fd:
                self.deletion_features[fn].append(fd[fn])

    def computeTTest(self):
        self.insertion_mean = {}
        self.deletion_mean = {}
        self.ttestResult = {}
        for fn in self.insertion_features:
            insertion_vs = self.insertion_features[fn]
            deletion_vs = self.deletion_features[fn]
            _, ttest_result = stats.ttest_ind(rvs1, rvs2, equal_var=False)
            self.ttestResult[fn] = ttest_result
            self.insertion_mean[fn] = np.mean(np.array(insertion_vs))
            self.deletion_mean[fn] = np.mean(np.array(deletion_vs))

    def generate2CSV(self, fileName):
        f = open(fileName, 'w')
        for fn in self.insertion_mean:
            # build print line
            line = ''
            line += fn
            line += ','
            line += 'Deletion_mean:'
            line += ','
            line += str(self.deletion_mean[fn])
            line += ','
            line += 'Insertion_mean:'
            line += ','
            line += str(self.insertion_mean[fn])
            line += ','
            line += 'ttest:'
            line += str(self.ttestResult[fn])
            line += '\n'
            f.write(line)
        f.close()


