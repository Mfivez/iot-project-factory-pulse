"""Point d'extension OpenCV : pastille verte, rouge ou inconnue."""

import cv2
import numpy as np


def detect_marker_color(*args, **kwargs):

    webcam = cv2.VideoCapture(0)

    while True:

        ret, frame = webcam.read()

        hsvFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        red_lower = np.array([0, 100, 100], np.uint8)
        red_upper = np.array([10, 255, 255], np.uint8)

        red_lower_high = np.array([170, 100, 100], np.uint8)
        red_upper_high = np.array([180, 255, 255], np.uint8)

        red_mask = cv2.bitwise_or(
            cv2.inRange(hsvFrame, red_lower, red_upper),
            cv2.inRange(hsvFrame, red_lower_high, red_upper_high),
        )

        # green color
        green_lower = np.array([35, 100, 100], np.uint8)
        green_upper = np.array([85, 255, 255], np.uint8)

        green_mask = cv2.inRange(hsvFrame, green_lower, green_upper)

        kernal = np.ones((5, 5), "uint8")

        # red color

        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernal)
        red_mask = cv2.dilate(red_mask, kernal)

        # green color
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernal)
        green_mask = cv2.dilate(green_mask, kernal)

        # Creating contour to track red color
        contours, hierarchy = cv2.findContours(
            red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                cv2.putText(
                    frame,
                    "Red Colour",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                )

        # Creating contour to track green color
        contours, hierarchy = cv2.findContours(
            green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.putText(
                    frame,
                    "Green Colour",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                )

        cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    webcam.release()
    cv2.destroyAllWindows()
