import numpy as np
from cv2 import VideoCapture, imshow


class LEDTracker:
    def __init__(self, tracked_channels = {'r': True, 'g': True, 'b': True}, thresholds = {'r': 128, 'g': 128, 'b': 128}, roi = None):
        """ Track up to three LEDs in red, blue or green color.
            
        Args:
            tracked_channels - dictionary indicating which of RGB channels to track
            thresholds - dictionary with thresholds for all three channels
            roi - region of interest to crop out of original video, specified as tuple (T, L, B, R) of top, left, bottom and right position
        """
        self.__camera = VideoCapture(0)
        self.__tracked_channels = tracked_channels
        self.__thresholds = thresholds
        self.__roi = roi

    def __del__(self):
        self.__camera.release()

    def track(self, send_message):
        """ Perform LED tracking.

        Return:
            Position of LEDs in each frame.
        """

        trajectories = {'r': [], 'b': [], 'g': []}

        while self.__camera.isOpened():
            read_successfuly, frame = self.__camera.read()
            if not read_successfuly:
                break

            cropped_frame = self.__crop_frame(frame, self.__roi)
            b_frame, g_frame, r_frame = cv2.split(cropped_frame)

            mouse_centre, pf = self.__detect_LED(cropped_frame, self.thresholds['r'])

            if self.__tracked_channels['r']:
                r_position = self.__detect_LED(r_frame, self.threshold['r'])
                trajectories['r'].append(r_position)

            if self.__tracked_channels['g']:
                g_position = self.__detect_LED(g_frame, self.threshold['g'])
                trajectories['g'].append(g_position)

            if self.__tracked_channels['b']:
                b_position = self.__detect_LED(b_frame, self.threshold['b'])
                trajectories['b'].append(b_position)

            send_message({'r': r_position, 'g': g_position, 'b': b_position})

        return trajectories

    def __detect_LED(self, frame, threshold):
        """ Detect mouse in a frame.

        Args:
            frame - frame
            threshold - threshold

        Return:
            LED position (x, y)
        """

        MAX_VAL = 255
        thresholded = cv2.threshold(frame, threshold, MAX_VAL, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(preprocessed_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour_idx = np.argmax([cv2.contourArea(c) for c in contours])
        return self.__compute_center(contours[largest_contour_idx])

    def __crop_frame(self, frame, roi):
        """ Crop given roi out of frame. 
        Args:
            roi - region of interest to crop out of original video, specified as tuple (T, L, B, R) of top, left, bottom and right position
        """
        return frame[roi[0]:roi[2], roi[1]:roi[3], :] if roi is not None else frame

    def __compute_center(self, contour):
        """ Compute center of the given contour.

        Args:
            contour - cv2 contour

        Return:
            center cooridnates (x, y)
        """
        m = cv2.moments(contour)
        return int(m["m10"] / (m["m00"] + 1e-6)), int(m["m01"] / (m["m00"] + 1e-6))


tracker = LEDTracker()

trajectories = tracker.track(lambda x: x)
