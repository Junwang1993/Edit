import cv2
import Time
import copy
class EditingTimeWindowVisualization(object):
    def preprocessing(self):
        # make sure video at index 0 is less than gaze at index 0
        flag = Time.Time().compareTwoTime(self.video_ats[self.index_video], self.gaze_ats[self.index_gaze])
        while flag>0:
            self.index_gaze += 1
            flag = Time.Time().compareTwoTime(self.video_ats[self.index_video], self.gaze_ats[self.index_gaze])

    def __init__(self, video_ats, video_cap, video_index_range, gaze_ats, gaze_info_list, gaze_index_range):
        # video related parameters
        self.video_ats = video_ats
        self.video_cap = video_cap

        self.video_index_range = video_index_range
        # gaze related parameters
        self.gaze_ats = gaze_ats
        self.gaze_info_list = gaze_info_list
        self.gaze_index_range = gaze_index_range
        # some index to access elements in the list
        self.index_video = self.video_index_range[0]
        self.index_gaze = self.gaze_index_range[0]
        self.preprocessing()
        # start flag
        self.flag = True
        # current frame
        self.currentFrame = None

        # visualization
        self.process_visualization()

    def process_visualization(self):
        ending = False
        while ending == False:
            if self.flag == True:
                # set next frame
                self.video_cap.set(1, self.index_video)
                # read video frame
                _, self.currentFrame = self.video_cap.read()
                self.flag = False
                #update
                self.index_video += 1
            else:
                #
                copy_currentFrame = None
                flag = Time.Time().compareTwoTime(self.video_ats[self.index_video], self.gaze_ats[self.index_gaze])
                if flag < 0:
                    # video is front ---
                    # set next frame
                    self.video_cap.set(1, self.index_video)
                    # read video frame
                    _, self.currentFrame = self.video_cap.read()
                    # update
                    self.index_video += 1
                else:
                    # gaze is front ---
                    # copy frame
                    copy_currentFrame = copy.deepcopy(self.currentFrame)
                    # get gaze info
                    gaze_x = self.gaze_info_list[0][self.index_gaze]
                    gaze_y = self.gaze_info_list[1][self.index_gaze]
                    # update index
                    self.index_gaze+=1
                    # draw

                    cv2.circle(copy_currentFrame, (int(1680.0*gaze_x), int(1050.0*gaze_y)), 5, (0, 0, 255), -1)
                    # show
                    cv2.imshow('frame', copy_currentFrame)  # show frame
                    # break point
                    if cv2.waitKey(100) & 0xFF == ord('q'):
                        break
                # checking whether
                if self.index_gaze > self.gaze_index_range[1]:
                    ending = True
                if self.index_video > self.video_index_range[1]:
                    ending = True






