"""OpenCV drawing helpers for pose visualization."""

import cv2


def draw_dotted_line(frame, point, start, end, line_color):
    x = point[0]
    for y in range(start, end, 10):
        if y + 5 < end:
            cv2.line(frame, (x, y), (x, y + 5), line_color, 2)
