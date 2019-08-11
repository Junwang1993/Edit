import Time
import FixationDetection

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

class FeaturesNearEditingPointModule(object):
    def __init__(self, ats_gaze, xs_gaze, ys_gaze, ats_kb, keyInfo_kb, editingAtRange, caretATs, caretPs, writingPositionATs, writingPositionPs, f_delta_at=500, b_delta_at=500):
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
        self.caretPs = caretPs
        self.writingPositionATs = writingPositionATs
        self.writingPositionPs = writingPositionPs
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
                ti_kb = ti_kb
            )
            self.editingIndexRange.append(ei)


    def extractFixationFeatures(self, ats_inRange, xs_inRange, ys_inRange):
        # all features --- dict
        fixation_fvl = {
            # fixation features go here!
            'allFixationDur': [],
            ''

        }
        # build rts
        rts_inRange = ConvertATs2RTs(ats_inRange)
        # detect fixation
        _, _, EfixTuple_index = FixationDetection.fixation_IDT_V2(xs_inRange, ys_inRange, rts_inRange)
        # iterate all fixations
        for i in range(0, len(EfixTuple_index)):
            # one fixation
            f_f_i = EfixTuple_index[i][0]
            f_b_i = EfixTuple_index[i][1]+1
            # fixation duration
            f_dur = rts_inRange[f_b_i] - rts_inRange[f_f_i]







