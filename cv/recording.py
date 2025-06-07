import os
import cv2 as cv
from datetime import datetime
from time import time

class Recording:
    def __init__(self):
        self.camera = cv.VideoCapture(0)

    def start_recording(self, cam_index, save_folder = ".", vid_len = 60, fps = 30):
        cam = self.camera
        if cam.isOpened():
            frame_width = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))
            if fps == 0:
                fps = cam.get(cv.CAP_PROP_FPS)
                if fps == 0:
                    fps = 30
            time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            out = cv.VideoWriter(f"{save_folder}/{time_now}.mp4", cv.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

        start_time = time()
        curr_time = start_time
        ret_val = 1
        while cam.isOpened() and curr_time-start_time < vid_len:
            ret, frame = cam.read()
            if ret:
                out.write(frame)
                # cv.imshow('Frame', frame)
                if cv.waitKey(1) & 0xFF == ord('q'):
                    ret_val = 0
                    break
            else:
                raise Exception("Something went wrong with cam")
            curr_time = time()
        out.release()
        cv.destroyAllWindows()

        print(f"{time_now}.mp4 saved!")
        return ret_val

    def start_refresh_recording(self, cam_index, vid_len = 10, fps = 30):
        cam = self.camera
        time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        os.makedirs(time_now)
        while cam.isOpened():
            ret = self.start_recording(0, time_now, vid_len)
            if not ret:
                break
        cam.release()
    

    def stop_recording(self):
        return None

if __name__ == "__main__":
    camera = Recording()
    camera.start_refresh_recording(0)
