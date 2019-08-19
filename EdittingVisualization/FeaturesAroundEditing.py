import Time
import FixationDetection
import numpy as np
import Editting

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

    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, editingType,caretATs, caretXs, caretYs, writingPositionATs, writingPositionXs, writingPositionYs, deltaT = 1000):
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
        self.preprocess_extract_editingRangeIndex()
        self.process()

    def process(self):
        self.fvs = []
        self.lbs = []
        for i in range(0, len(self.editingIndexRange)):
            ei = self.editingIndexRange[i]
            # extracting features
            fvl = self.extractFixationFeaturesList(
                ats_inRange_gaze = self.ats_gaze[ei.f_full_gaze:ei.b_full_gaze],
                xs_inRange_gaze = self.xs_gaze[ei.f_full_gaze:ei.b_full_gaze],
                ys_inRange_gaze = self.ys_gaze[ei.f_full_gaze:ei.b_full_gaze],
                ats_inRange_cursor = self.caretATs[ei.f_full_gaze:ei.b_full_gaze],
                xs_inRange_cursor = self.caretXs[ei.f_full_gaze:ei.b_full_gaze],
                ys_inRange_cursor = self.caretYs[ei.f_full_gaze:ei.b_full_gaze]
            )
            fv, self.fv_name = self.extractFixationFeaturesVector()
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

    def preprocess_extract_editingRangeIndex(self):
        self.editingIndexRange = []
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

    def extractFixationFeaturesList(self, ats_inRange_gaze, xs_inRange_gaze, ys_inRange_gaze,
                                ats_inRange_cursor, xs_inRange_cursor, ys_inRange_cursor):
        # initial holder
        self.fixation_fvl = {
            'allFixationDur': [],
            'allFixationPositionType1':[], # ahead or behind
            'allFixationPositionType2':[],
            'd2c_x': [],
            'd2c_y': []
        }
        # build rts
        rts_inRange_gaze = ConvertATs2RTs(ats_inRange_gaze)
        # detect fixation
        _, _, EfixTuple_index = FixationDetection.fixation_IDT_V2(xs_inRange_gaze, ys_inRange_gaze, rts_inRange_gaze)
        # iterate all fixations
        for i in range(0, len(EfixTuple_index)):
            # one fixation
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