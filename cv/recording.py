import os
import cv2 as cv
from datetime import datetime
from time import time, sleep
from gpiozero import Button

class Recording:
    def __init__(self):
        self.camera = cv.VideoCapture(0)
        self.button = Button(17)
        self.button_fg = 0
        self.ret_val = 1

    def start_recording(self, save_folder = ".", vid_len = 60, fps = 30):
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
        self.ret_val = 1
        while cam.isOpened() and curr_time-start_time < vid_len:
            if self.button.is_pressed:
                while self.button.is_pressed:
                    sleep(.001)
                self.button_fg = 1
            ret, frame = cam.read()
            if ret:
                out.write(frame)
                # cv.imshow('Frame', frame)
                if self.button_fg == 1:
                    self.button_fg = 0
                    self.ret_val = 0
                    break
            else:
                raise Exception("Something went wrong with cam")
            curr_time = time()
        out.release()
        cv.destroyAllWindows()

        print(f"{time_now}.mp4 saved!")

    def start_refresh_recording(self, vid_len = 10, fps = 30):
        cam = self.camera
        while 1:
            time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            os.makedirs(time_now)
            self.button.wait_for_press()
            while self.button.is_pressed:
                sleep(.001)
            print("recording started")
            while cam.isOpened():
                self.start_recording(time_now, vid_len)
                if not self.ret_val:
                    print("recording stopped")
                    break
        cam.release()
    

    def stop_recording(self):
        return 0

if __name__ == "__main__":
    camera = Recording()
    camera.start_refresh_recording()
