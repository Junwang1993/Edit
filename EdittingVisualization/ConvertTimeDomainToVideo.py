import Time
class ConvertTimeDomainToVideo(object):
    @staticmethod
    def convertTimeDomain2Video(time_other, time_vidoe, collections_data):
        startIndex = -1
        endIndex = -1
        #time_other = [Time.Time(i) for i in time_other]
        #time_vidoe = [Time.Time(i) for i in time_vidoe]
        collections_data_converted = []
        for i in range (0, len(collections_data)):
            collections_data_converted.append([])
        lastPosition = 0
        for i in range (0, len(time_vidoe)):
            # get one time in other dimension
            t = time_vidoe[i]
            # find position in video dimension
            p = Time.Time().findPositionInTimeArray(t, time_other,lastPosition=lastPosition)
            # check it is not outside the video
            lastPosition = p
            if p<=0:
                startIndex = i
            if p>=len(time_other) and endIndex==-1:
                endIndex = i
            if p>0 and p<len(time_other):
                t_l = time_other[p-1]
                t_n = time_other[p]
                total_difference_time = Time.Time().substractionBetweenTwoTime(t_l, t_n)
                t_difference_time = Time.Time().substractionBetweenTwoTime(t_l, t)
                for j in range(0, len(collections_data)):
                    v_l = collections_data[j][p-1]
                    v_n = collections_data[j][p]
                    v = v_l + ((float(v_n) - float(v_l))/float(total_difference_time))*float(t_difference_time)
                    collections_data_converted[j].append(v)
        if endIndex == -1:
            endIndex = 0
        return startIndex+1, endIndex-1, collections_data_converted

    @staticmethod
    def InsertInterpolateListBack(insert_ats, full_ats, insertData, fullData):
        # insert is video at
        # full is gaze at
        refine_ats = []
        refine_data = []
        for i in range(0, len(insertData)):
            refine_data.insert([])
        # two index
        i_insert = 0
        i_full = 0
        while True:
            if i_insert == -1 and i_full == -1:
                # ending point
                break
            else:
                if i_insert>=0 and i_full>=0:
                    at_insert = insert_ats[i_insert]
                    at_full = full_ats[i_full]
                    # compare who is larger
                    flag = Time.Time.compareTwoTsime(at_insert, at_full)
                    if flag <0:
                        # at_insert is less
                        refine_ats.append(at_insert)
                        for i_d in range(0, len(insertData)):
                            refine_data[i_d].append(insertData[i_d][i_insert])
                        # update
                        i_insert+=1
                        if i_insert>=len(insert_ats):
                            i_insert = -1

                    elif flag == 0:
                        # both equal
                        refine_ats.append(at_insert)
                        for i_d in range(0, len(insertData)):
                            refine_data[i_d].append(insertData[i_d][i_insert])
                        # update
                        i_insert+=1
                        if i_insert>=len(insert_ats):
                            i_insert = -1
                        i_full +=1
                        if i_full>=len(full_ats):
                            i_full =-1

                    else:
                        # at_full is less
                        refine_ats.append(at_full)
                        for i_d in range(0, len(insertData)):
                            refine_data[i_d].append(fullData[i_d][i_full])
                        # update
                        i_full+=1
                        if i_full>=len(full_ats):
                            i_full =-1
                elif i_insert>=0:
                    refine_ats.append(at_insert)
                    for i_d in range(0, len(insertData)):
                        refine_data[i_d].append(insertData[i_d][i_insert])
                    # update
                    i_insert += 1
                    if i_insert >= len(insert_ats):
                        i_insert = -1
                else:
                    refine_ats.append(at_full)
                    for i_d in range(0, len(insertData)):
                        refine_data[i_d].append(fullData[i_d][i_full])
                    # update
                    i_full += 1
                    if i_full >= len(full_ats):
                        i_full  =-1

        return refine_ats, refine_data


