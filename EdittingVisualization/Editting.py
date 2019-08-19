import numpy as np
import Time

def getCursorPosition(at_wanted, ats_cursor, xs_cursor, ys_cursor, length = 1680.0, width = 1050.0):
    # found index need to substract one
    i = Time.Time().findPositionInTimeArray(at_wanted, ats_cursor)-1
    # refine index
    if i <0:
        i = 0
    if i >= len(ats_cursor):
        i = len(ats_cursor)-1
    if i == -1:
        i = len(ats_cursor)-1
    # cursor position tuple
    cursor_p = (xs_cursor[i], ys_cursor[i])
    return cursor_p

def readEditingIntervalsCSV(fileName):
    editingInterval = []
    editingType = []
    with open(fileName, 'r') as f:
        for line in f:
            line_info = line.split(',')
            interval_f_at = Time.Time(line_info[0])
            interval_b_at = Time.Time(line_info[1])
            type = line_info[2]
            # append
            editingInterval.append((interval_f_at, interval_b_at))
            editingType.append(type)
    return editingInterval, editingType

class CaretPositionModule(object):
    def __init__(self, ats_c, xs_c, ys_c):
        # inner parameter
        self.ats_c = ats_c
        self.xs_c = xs_c
        self.ys_c = ys_c

    def getCurrentCaretPosition(self, at_check):
        index_c = Time.Time().findPositionInTimeArray(at_check, self.ats_c)-1
        if index_c<0:
            index_c = 0
        if index_c>=len(self.ats_c):
            index_c = len(self.ats_c)-1
        return (self.xs_c[index_c], self.ys_c[index_c])

    def getCurrentSeriesCaretPosition(self, at_check, num_following = 2):
        index_found = self.getCurrentCaretIndex(at_check)
        index_b = index_found + num_following
        # refine index
        refine_index = []
        for i in range(index_found, index_b+1):
            if i<0:
                refine_index.append(0)
            elif i> len(self.ats_c)-1:
                refine_index.append(len(self.ats_c)-1)
            else:
                refine_index.append(i)
        refine_positions = []
        for position_index in refine_index:
            refine_positions.append((self.xs_c[position_index],self.ys_c[position_index]))
        return refine_positions

    def getCurrentCaretIndex(self, at_check):
        index_c = Time.Time().findPositionInTimeArray(at_check, self.ats_c) - 1
        if index_c < 0:
            index_c = 0
        if index_c >= len(self.ats_c):
            index_c = len(self.ats_c) - 1
        return index_c



class WritingPositionModule(object):
    def __init__(self, ats_wp, xs_wp, ys_wp):
        # inner parameter
        self.ats_wp = ats_wp
        self.xs_wp = xs_wp
        self.ys_wp = ys_wp
    def getCurrentWritingPlace(self, at_check):
        index_wp = Time.Time().findPositionInTimeArray(at_check, self.ats_wp)-1
        if index_wp<0:
            index_wp = 0
        if index_wp>=len(self.ys_wp)-1:
            index_wp = len(self.ys_wp)-1
        # if index_wp == -1:
        #     index_wp = len(self.ys_wp) - 1
        return  (self.xs_wp[index_wp], self.ys_wp[index_wp])

class CursorPositionModule(object):
    def __init__(self, ats_cp, xs_cp, ys_cp):
        # inner parameter
        self.ats_cp = ats_cp
        self.xs_cp = xs_cp
        self.ys_cp = ys_cp
    def getCurrentWritingPlace(self, at_check):
        index_cp = Time.Time().findPositionInTimeArray(at_check, self.ats_cp)-1
        if index_cp<0:
            index_cp = 0
        if index_cp>=len(self.ys_cp)-1:
            index_cp = len(self.ys_cp)-1
        # if index_wp == -1:
        #     index_wp = len(self.ys_wp) - 1
        return  (self.xs_cp[index_cp], self.ys_cp[index_cp])

class EditingModule(object):
    def __init__(self, ats_cursor, xs_cursor, ys_cursor, writing_position_module):
        # holder
        self.insertion_at_list = []
        # inner parameter
        self.ats_cursor = ats_cursor
        self.xs_cursor = xs_cursor
        self.ys_cursor = ys_cursor
        # build caret module
        self.cpm = CaretPositionModule(self.ats_cursor, self.xs_cursor, self.ys_cursor)
        # build writing position module
        self.wpm = writing_position_module
        # preprocessing
        self.ExtractFullEdittingIntervals()
        self.determineTypeOfEditing()

    def ExtractFullEdittingIntervals(self, characterWidth = 10, lineHeight = 80):
        # full means: moving back caret (maybe multiple moving) then i
        #             insert new info than move to current place


        # parameters to find editing interval
        start_movingBack = None
        start_typing = None
        start_typing_p = None
        start_movingCurrent = None



        FullEdittingIntervals = []
        FullEdittingTypingPositions = []
        sequence_ys = []

        current_caret_position = (self.xs_cursor[0], self.ys_cursor[0])
        current_writing_position = self.wpm.getCurrentWritingPlace(self.ats_cursor[0])
        if current_writing_position ==(0,0):
            current_writing_position =(self.xs_cursor[0], self.ys_cursor[0])

        # start to iterate
        for i in range(1, len(self.ats_cursor)):
            print(str(i))
            next_at = self.ats_cursor[i]
            next_caret_x = self.xs_cursor[i]
            next_caret_y = self.ys_cursor[i]
            # get writing position
            current_writing_position = self.wpm.getCurrentWritingPlace(self.ats_cursor[i])
            if current_writing_position == (0, 0):
                current_writing_position = (self.xs_cursor[i], self.ys_cursor[i])



            d_x_wp = current_writing_position[0]-next_caret_x
            d_y_wp = current_writing_position[1]-next_caret_y
            d_x_c = current_caret_position[0] -next_caret_x
            d_y_c = current_caret_position[1] - next_caret_y


            if ((d_x_c >= characterWidth and (d_y_c)>=-5) or d_y_c >= lineHeight):
                # moving backard
                if start_movingBack == None:
                    start_movingBack = i-2



            elif abs(d_x_c)<=10 and abs(d_y_c)<=20:
                # not moving
                pass

            else:
                # moving forward
                # check whether it has already moving back to current writing place

                if (next_caret_y+10>=current_writing_position[1]+lineHeight) or (abs(next_caret_y-current_writing_position[1])<=20 and next_caret_x+10>=current_writing_position[0]):
                    if start_movingBack != None:
                        start_movingCurrent = i
                        # adding
                        if start_typing != None:
                            FullEdittingIntervals.append((self.ats_cursor[start_movingBack], self.ats_cursor[start_movingCurrent],self.ats_cursor[start_typing]))
                            FullEdittingTypingPositions.append(start_typing_p)
                        else:
                            FullEdittingIntervals.append((self.ats_cursor[start_movingBack],
                                                          self.ats_cursor[start_movingCurrent],
                                                          None))
                            FullEdittingTypingPositions.append(None)
                        if len(FullEdittingIntervals) == 6:
                            print('dd')
                        sequence_ys.append(self.ys_cursor[start_movingBack:start_movingCurrent+1])
                        # reassign
                        start_movingBack = None
                        start_typing = None
                        start_typing_p =None
                        start_movingCurrent = None

                elif start_movingBack != None and start_typing == None:
                        start_typing = i
                        start_typing_p = (next_caret_x, next_caret_y)
            # update caret position
            current_caret_position = (next_caret_x, next_caret_y)

        self.FullEdittingIntervals = FullEdittingIntervals
        self.FullEdittingTypingPostions = FullEdittingTypingPositions

        print('d')

    def AreTwoPointsClose(self, p1, p2, thres_x=30, thres_y=20):
        # true is close
        # false is not close
        if abs(p1[0]-p2[0])<=thres_x and abs(p1[1]-p2[1])<=thres_y:
            return True
        else:
            return False

    def determineTypeOfEditing(self):
        # Types: insertion, deletion
        # Tuple: at_moving_back, at_moving_toCurren, at_typing
        self.editingTypes = []
        for i in range(0, len(self.FullEdittingIntervals)):
            tuple = self.FullEdittingIntervals[i]
            if tuple[-1] == None:
                self.editingTypes.append('Deletion')
            else:
                # check writing position...
                cwP = self.wpm.getCurrentWritingPlace(tuple[-1])
                # ckeck series of caret positions
                caretPs = self.cpm.getCurrentSeriesCaretPosition(tuple[-1], num_following=2)
                flag_close = True
                for caretP in caretPs:
                    flag = self.AreTwoPointsClose(cwP, caretP)
                    if flag == False:
                        flag_close = False
                        break
                if not flag_close:
                    self.editingTypes.append('Insertion')
                else:
                    self.editingTypes.append('Deletion')

    def generate2CSV(self, fileName):
        f = open(fileName, 'w')
        for i in range(0, len(self.FullEdittingIntervals)):
            interval = self.FullEdittingIntervals[i]
            type = self.editingTypes[i]
            line = ''
            line += Time.Time().toString(interval[0])
            line += ','
            line += Time.Time().toString(interval[1])
            line += ','
            line += type
            f.write(line)
            f.write('\n')
        f.closed





