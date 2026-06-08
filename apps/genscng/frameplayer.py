
import time
import os

# ------------------------------------------------------------------------------

class FramePlayer():

    def __init__(self,
                 filename=None,
                 fileext="jpeg",
                 timeinter=5):
        
        self.filename = filename
        self.fileext = fileext
        self.timeinter = timeinter

        self.current = 0      
        self.lastcall=time.time()


    def next(self):
        frame = None
        if self.filename:
            filename = self.filename + str(self.current) + "." + self.fileext
            if os.path.isfile(filename):
                frame = filename
                waittime = self.timeinter - (time.time() - self.lastcall)
                if waittime > 0:
                    time.sleep(waittime)
                    self.lastcall = time.time()
                    self.current = self.current + 1
        return frame

# ------------------------------------------------------------------------------


if __name__ == "__main__":

    frameplayer = FramePlayer()

    fnext = frameplayer.next()
    while fnext:
        print(str(time.time()) + " " + fnext)
        fnext = frameplayer.next()

    exit(0)
