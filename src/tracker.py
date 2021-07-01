from argparse import ArgumentParser
import numpy as np
import cv2
from pythonosc.udp_client import SimpleUDPClient


class LEDTracker:
    def __init__(self, thresholds={'r': 128, 'g': 128, 'b': 128}, frame_rate=60, frame_size=None, roi=None):
        """ Track up to three LEDs in red, blue or green color.
            
        Args:
            thresholds - dictionary with thresholds for all three channels
            frame_rate - frames per second
            frame_size - tuple (widht, height)
            roi - region of interest to crop out of original video, specified as tuple (T, L, B, R) of top, left, bottom and right position
        """
        self.__thresholds = thresholds
        self.__roi = roi

        self.__camera = cv2.VideoCapture(0)
        self.__camera.set(cv2.CAP_PROP_FPS, frame_rate)

        if frame_size is not None:
            self.__camera.set(cv2.CAP_PROP_FRAME_WIDTH, frame_size[0])
            self.__camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_size[1])
            
        self.__frame_size = (self.__camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.__camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def __del__(self):
        self.__camera.release()

    def track(self, send_message):
        """ Perform LED tracking.

        Args:
            send_message - function that gets position and frame size and frowards a message for each frame
        Return:
            Position of LEDs in each frame.
        """

        trajectories = {}
        positions = {}

        for c in self.__thresholds.keys():
            trajectories[c] = []
            positions[c] = None

        while self.__camera.isOpened():
            read_successfuly, frame = self.__camera.read()
            if not read_successfuly:
                break

            cropped_frame = self.__crop_frame(frame, self.__roi)
            b_frame, g_frame, r_frame = cv2.split(cropped_frame)
            color_planes = {'r': r_frame, 'g': g_frame, 'b': b_frame}

            for c, t in self.__thresholds.items():
                position = self.__detect_LED(color_planes[c], t)
                trajectories[c].append(position)
                positions[c] = position

            send_message(positions, self.__frame_size)

            cv2.imshow("video in", cropped_frame)
            cv2.waitKey(0)

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
        thresholded = cv2.threshold(frame, threshold, MAX_VAL, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresholded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return (-1, -1)
        largest_contour_idx = np.argmax([cv2.contourArea(c) for c in contours])
        return self.__compute_center(contours[largest_contour_idx])

    def __compute_center(self, contour):
        """ Compute center of the given contour.

        Args:
            contour - cv2 contour

        Return:
            center cooridnates (x, y)
        """
        m = cv2.moments(contour)
        return int(m["m10"] / (m["m00"] + 1e-6)), int(m["m01"] / (m["m00"] + 1e-6))

    def __crop_frame(self, frame, roi):
        """ Crop given roi out of frame. 
        Args:
            roi - region of interest to crop out of original video, specified as tuple (T, L, B, R) of top, left, bottom and right position

        Return:
            cropped frame
        """
        return frame[roi[0]:roi[2], roi[1]:roi[3], :] if roi is not None else frame

class MessageSender:
    def __init__(self, server_address="localhost", pixel_coords=False, ports={'r': 1, 'g': 2, 'b': 3}):
        """ OSC client that sends positions provided by LEDTracker.

        Args:
            server_address - ip address of a server receiving positions
            pixel_coords - whether to send position in pixel coords (False by default, use 0-1 range)
            ports - ports for red, blue and green positions
        """
        self.__pixel_coords = pixel_coords
        self.__clients = {}
        for c, p in ports.items():
            self.__clients[c] = SimpleUDPClient(server_address, p)

    def send_message(self, positions, frame_size):
        """ Send message given position and frame size.

        Args:
            positions - dictionary of (x,y) position to send (with 'r', 'g', 'b' keys)
            frame_size - tuple (widht, height)
        """

        print(positions)
        for c, p in positions.items():
            self.__clients[c].send_message(f"/{c}", self.__prepare_message(p, frame_size))

    def __prepare_message(self, position, frame_size):
        """ Prepare message in appropriate format.

        Args:
            position - (x,y) position to send
            frame_size - tuple (widht, height)

        Return:
            Message to be sent - tuple
        """
        if self.__pixel_coords or position == (-1, -1):
            p = (float(position[0]), float(position[1]))
        else:
            p = (position[0] / frame_size[0], position[1] / frame_size[1])

        return (*p, *frame_size)



if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("--server_address", type=str, default="localhost", help="ip address of a server receiving positions.")
    args.add_argument("--pixel_coords", type=bool, default=False, help="Whether to send position in pixel coords (False by default, use 0-1 range).")
    args.add_argument("--r_port", type=int, default=1, help="Port for red LED data.")
    args.add_argument("--g_port", type=int, default=2, help="Port for green LED data.")
    args.add_argument("--b_port", type=int, default=3, help="Port for blue LED data.")
    args.add_argument("--r_thr", type=int, default=228, help="Detection threshold for red LED (0-255 range).")
    args.add_argument("--g_thr", type=int, default=228, help="Detection threshold for green LED (0-255 range).")
    args.add_argument("--b_thr", type=int, default=228, help="Detection threshold for blue LED (0-255 range).")
    args.add_argument("--frame_rate", type=int, default=60, help="Frame rate to use for the camera.")
    args.add_argument("--resolution", type=int, nargs=2, default=None, help="Resolution (width, height) for the camera.")
    args.add_argument("--roi", type=int, nargs=4, default=None, help="Region of interest to crop out of original video, specified as tuple (T, L, B, R) of top, left, bottom and right position.")
    args = args.parse_args()

    sender = MessageSender(args.server_address, args.pixel_coords, ports={'r':args.r_port, 'b':args.g_port, 'b':args.b_port})
    tracker = LEDTracker({'r':args.r_thr, 'b':args.g_thr, 'b':args.b_thr}, args.frame_rate, args.resolution, args.roi)

    trajectories = tracker.track(sender.send_message)

