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

