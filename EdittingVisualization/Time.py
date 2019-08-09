import re
class Time(object):
    def __init__(self, time_string = ''):
        if time_string != '':
            timeParts = time_string.split(':')
            whiteSpace = re.compile(r'\s+')
            self.h = float(re.sub(whiteSpace, '', timeParts[0]))
            self.m = float(re.sub(whiteSpace, '', timeParts[1]))
            self.s = float(re.sub(whiteSpace, '', timeParts[2]))
            self.ms = float(re.sub(whiteSpace, '', timeParts[3]))

    @staticmethod
    def substractByNms(t, nms):
        h = t.h
        m = t.m
        s = t.s
        ms = t.ms
        ms = ms - nms
        while ms < 0:
            s = s - 1
            ms = ms + 1000
        while s < 0:
            m = m - 1
            s = s + 60
        while m < 0:
            h = h - 1
            m = m + 60
        time_str = str(h) + ':' + str(m) + ':' + str(s) + ':' + str(ms)
        return Time(time_str)

    @staticmethod
    def addByNms(t, nms):
        h = t.h
        m = t.m
        s = t.s
        ms = t.ms
        ms = ms + nms
        while ms >= 1000:
            s = s + 1
            ms = ms - 1000
            while s >= 60:
                m = m + 1
                s = s - 60
                while m >= 60:
                    h = h + 1
                    m = m - 60
        time_str = str(h) + ':' + str(m) + ':' + str(s) + ':' + str(ms)
        return Time(time_str)

    @staticmethod
    def compareTwoTime(t1, t2):
        nms1 = t1.h * 60 * 60 * 1000 + t1.m * 60 * 1000 + t1.s * 1000 + t1.ms
        nms2 = t2.h * 60 * 60 * 1000 + t2.m * 60 * 1000 + t2.s * 1000 + t2.ms
        if nms1 > nms2:
            return 1
        elif nms1 == nms2:
            return 0
        else:
            return -1

    @staticmethod
    def findPositionInTimeArray(t, ts, lastPosition = 0):
        if lastPosition == len(ts):
            return len(ts)
        position = lastPosition
        c_t = ts[position]
        while Time.compareTwoTime(t, c_t) >= 0:
            position = position + 1
            if position >= len(ts):
                return len(ts)-1
            c_t = ts[position]
        return position

    @staticmethod
    def substractionBetweenTwoTime(t1, t2):
        nms1 = t1.h * 60 * 60 * 1000 + t1.m * 60 * 1000 + t1.s * 1000 + t1.ms
        nms2 = t2.h * 60 * 60 * 1000 + t2.m * 60 * 1000 + t2.s * 1000 + t2.ms
        return nms2 - nms1

    @staticmethod
    def generateRelativeTimeListFromAbsolut(T):
        relative = [0.0]
        for i in range(1, len(T)):
            diff = Time.substractionBetweenTwoTime(T[0], T[i])
            # if diff == relative[-1]:
            #     print('dsdsds')
            relative.append(diff)
        return relative

    @staticmethod
    def findPositionInFloatList(value, l, last=0):
        position = last
        while value >= l[position]:
            position = position + 1
            if position >= len(l):
                return len(l)-1
        return position

    @staticmethod
    def convertRtListToAtList(rt, at_first):
        at = []
        for i in range(0, len(rt)):
            at.append(Time.addByNms(at_first, int(rt[i])))
        return  at

    @staticmethod
    def toString(at):
        if at ==None:
            return 'None'
        return str(at.h)+str(':')+str(at.m)+str(':')+str(at.s)+str(':')+str(at.ms)

    @staticmethod
    def convertAtIntervelIntoIndex(at_intervel, ats, lastFound = 0):
        at_start = at_intervel[0]
        at_end = at_intervel[1]
        index_intervel_s = Time().findPositionInTimeArray(at_start, ats, lastFound)
        lastFound =index_intervel_s
        index_intervel_e = Time().findPositionInTimeArray(at_end, ats,lastFound)
        return (index_intervel_s-1, index_intervel_e-1)

    @staticmethod
    def convertAtIntervalListToRtInterval(AIL, at_first):
        RTL = []
        for I in AIL:
            start = I[0]
            diff1 = Time().substractionBetweenTwoTime(at_first, start)
            end = I[1]
            diff2 = Time().substractionBetweenTwoTime(at_first, end)
            RTL.append((diff1, diff2))
        return RTL


    @staticmethod
    def enlargeRtSubListTwoSides(rt_full, rt_sub, f_nm, b_nm):
        # rt list after enlarging
        frt = rt_sub[0] - f_nm
        brt = rt_sub[-1] + b_nm
        if frt<0:
            frt = 0
        if brt>rt_full[-1]:
            brt = rt_full[-1]
        # find index
        fidx = Time.findPositionInFloatList(frt, rt_full)-1
        bidx = Time.findPositionInFloatList(brt, rt_full)
        # two things
        return rt_full[fidx:bidx], (fidx, bidx)

    @staticmethod
    def isRtIntervalInARTIntervalList(rti_check, rti_list):
        rt1 = rti_check[0]
        rt2 = rti_check[1]

        for rti in rti_list:
            s = rti[0]
            e = rti[1]
            if s<= rt1 and rt1<=e and s<= rt2 and rt2<=e:
                return True
        return False
