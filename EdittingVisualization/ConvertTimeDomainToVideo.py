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



