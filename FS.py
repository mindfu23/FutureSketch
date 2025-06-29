import ImageToDMX as imdmx
import numpy as np
import time

receivers = [
            # Primary display receivers (frame 0)
            [
                {
                    'ip': '192.168.68.111',
                    'pixel_count': 500,
                    'addressing_array': imdmx.make_indicesHS(r"Unit1.txt")
                }
            ]]
dat = np.random.randint(0,255,(16,16,3)).astype(np.uint8)
dat=np.zeros([16,16,3]).astype(np.uint8)
dat[:,7,2]=255
screens = []
for i in range(len(receivers)):
    if i < len(receivers):
        screens.append(imdmx.SACNPixelSender(receivers[i]))
    else:
        # For displays without physical receivers, add None as placeholder
        screens.append(None)
while True:
    dat=dat*0.999
    time.sleep(1/20)





    screens[0].send(dat.copy().astype(np.uint8))