import numpy as np
import Time
# static method

class EditingModule():
    def __init__(self, ats_cursor, xs_cursor, ys_cursor):
        # holder
        self.insertion_at_list = []
        # inner parameter
        self.ats_cursor = ats_cursor
        self.xs_cursor = xs_cursor
        self.ys_cursor = ys_cursor
        # processing
        self.process_InsertingPoints()


    def isInserting(self, lastCursor, currentCursor, thres_x_diff = -20, thres_y_diff = -20):
        # cursor moving back
        if currentCursor[1] - lastCursor[1] <= thres_y_diff:
            return True
        elif currentCursor[0] - lastCursor[0] <= thres_x_diff:
            return True
        return False


    def process_InsertingPoints(self):
        for i in range(1, len(self.ats_cursor)):
            lastCursor = (self.xs_cursor[i-1], self.ys_cursor[i-1])
            currentCursor = (self.xs_cursor[i], self.ys_cursor[i])
            # info
            delta_y = (currentCursor[1] - lastCursor[1])
            delta_x = (currentCursor[0] - lastCursor[0])
            insert_flag = self.isInserting(lastCursor, currentCursor)
            if insert_flag == True:
                self.insertion_at_list.append(self.ats_cursor[i])

    def getInsertAtList(self):
        return self.insertion_at_list

    def getAllInertionTimeWindow(self, dt_front, dt_back):
        # return a at tuple list
        insertion_time_window_list = []
        for at in self.insertion_at_list:
            # generate time window
            tm = (Time.Time().substractByNms(at, dt_front), Time.Time().addByNms(at, dt_back))
            insertion_time_window_list.append(tm)
        return insertion_time_window_list

class EditingModule():
    def __init__(self, ats_cursor, xs_cursor, ys_cursor):
        # holder
        self.insertion_at_list = []
        # inner parameter
        self.ats_cursor = ats_cursor
        self.xs_cursor = xs_cursor
        self.ys_cursor = ys_cursor
        # processing
        self.process_InsertingPoints()


    def ExtractFullEdittingIntervals(self, characterWidth = 20, lineHeight = 20):
        # full means: moving back caret (maybe multiple moving) then i
        #             insert new info than move to current place


        # parameters to find editing interval
        start_movingBack = None
        start_typing = None
        start_movingCurrent = None

        FullEdittingIntervals = []
        current_caret_position = (self.xs_cursor[0], self.ys_cursor[0])
        # start to iterate
        for i in range(1, len(ats_cursor)):
            next_caret_x = self.xs_cursor[i]
            next_caret_y = self.ys_cursor[i]
            d_x = current_caret_position[0]-next_caret_x
            d_y = current_caret_position[1]-next_caret_y
            if d_x >= characterWidth or d_y >= lineHeight:
                # moving backard
                if start_movingBack != None:
                    start_movingBack = i
            elif abs(d_x)<=10 and abs(d_y)<=10:
                # not moving
                pass
            else:
                # moving forward
                # check whether it has already moving back to current caret

                if (next_caret_y+10>=current_caret_position[1]) or (next_caret_y+10>=current_caret_position[1] and next_caret_x+10>=current_caret_position[0]):
                    if start_movingBack != None:
                        start_movingCurrent = i
                        # adding
                        FullEdittingIntervals.append((start_movingBack, start_typing, start_movingBack))
                        current_caret_position = (next_caret_x, next_caret_y)

                if start_movingBack != None and start_movingCurrent == None:
                    if start_typing != None:
                        start_typing = i

        self.FullEdittingIntervals_index = FullEdittingIntervals


