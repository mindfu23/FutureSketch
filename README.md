# FutureSketch
Repo for scripts to control the LEDs for my interactive sculpture Future Sketch.

--2025-06-29--

Status:

16x16 WS8112 test grid receiving info thru Pixlite 4, displaying rows or columns as desired.

1st attached Rotary encoder outputting information, recieved by Beaglebones, sent through Pixlite to 16x16 test grid. 

Full X and Y from rotary encoder. Some possible skipping, fully acceptable even now in final product.

Output currently has option for slow fade. 

Next programming goals:
- save to SD as reproducible file for animation
- set up accelerometer to erase animation, replacing slow fade

Next physical goals:
- set up bank of at least a few hundred LEDs, with power suppplies
- set up all 4 sets of knobs with inputs to Beaglebones

Notes:
- may need to find the Beaglebones IP address again. Enter arp -a before I connect it, and then afterwards.
- current functionality includes a slow fade. Acceleromater shaking / erasing is currently post-MVP
- Pixlite 4 connected to 5v power supply output, as output into Pixlite 4 must match output to LEDs. When switch to 4000 LEDs, must switch power supply to Pixlite 4.
- All files starting with "Beaglebones_pixlite" are v1 test scripts, set 1. The one titled "_total.py" has the most options and some comments.

Reference:

Beaglebones pin diagram: https://toptechboy.com/beaglebone-black-lesson-1-understanding-beaglebone-black-pinout/beaglebone-black-pinout/

Rotary encoder info: 
https://forum.arduino.cc/t/no-datasheet-for-popular-encoder/942728/7
