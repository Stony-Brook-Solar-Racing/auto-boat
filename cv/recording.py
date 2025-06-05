import cv2 as cv
from datetime import datetime

class Recording:
    def __init__(self):
        self.camera = cv.VideoCapture(0)

    def start_recording(self, fps = 30):
        cam = self.camera
        if cam.isOpened():
            frame_width = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))
            if fps == 0:
                fps = cam.get(cv.CAP_PROP_FPS)
                if fps == 0:
                    fps = 30
            time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            out = cv.VideoWriter(f"{time}.mp4", cv.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

        while cam.isOpened():
            ret, frame = cam.read()
            if ret:
                out.write(frame)
                cv.imshow('Frame', frame)
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
        cam.release()
        out.release()
        cv.destroyAllWindows()

        print(f"{time}.mp4 saved!")
        return True

    def stop_recording(self):
        return None

if __name__ == "__main__":
    camera = Recording()
    camera.start_recording(30)
