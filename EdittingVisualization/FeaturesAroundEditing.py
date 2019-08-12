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
    return ats


def Refined_find_index_in_ATs(at, ats, lastFoundIndex):
    index =Time.Time().findPositionInTimeArray(at,ats, lastFoundIndex)
    if index<0:
        index = 0
    if index>=len(ats)-1:
        index = len(ats)-1
    return index



class EditingIndex(object):
    # ------f_full--(delta)--f_edit---t---b_edit--(delta)--b_full
    def __init__(self, f_full_gaze, f_edit_gaze, f_full_kb, f_edit_kb, b_full_gaze, b_edit_gaze, b_full_kb, b_edit_kb, t_gaze, t_kb):
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

    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, caretATs, caretXs, caretYs, writingPositionATs, writingPositionXs, writingPositionYs, deltaT = 1000):
        # gaze
        self.ats_gaze = ats_gaze
        self.xs_gaze = xs_gaze
        self.ys_gaze = ys_gaze
        # keyboard
        self.ats_kb = ats_kb
        self.keyInfo_kb = keyInfo_kb
        # editing
        self.editingAtRange = editingAtRange
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

    def preprocess_extract_editingRangeIndex(self):
        self.editingIndexRange = []
        # iterate all editing interval
        # iterating parameters
        lastFoundIndex_gaze = 0
        lastFoundIndex_kb = 0
        for i in range(0, len(self.editingAtRange)):
            one_edit_at_range = self.editingAtRange[i]
            editing_at_moment = one_edit_at_range[2] # at moment that start editing

