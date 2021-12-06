This is a quick python script that uses a motion detector to play audio from a speaker whenever someone moves near the sensor. 

There are two versions of this script:

 * `motion_detector_IR.py` uses an HC SR-501 PIR (or similar) motion-detecting sensor (see [https://lastminuteengineers.com/pir-sensor-arduino-tutorial/](https://lastminuteengineers.com/pir-sensor-arduino-tutorial/) for a quick tutorial) to trigger the system to play audio.

 * `motion_detector.py` uses an HC-SR04 (or similar) ultrasonic range detector (see [https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi](https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi) for a tutorial) to detect movement of an object directly in front of the sensor.


The motion detector and audio player are both implemented as separate threads so the main event loop can handle inputs from them while also monitoring a connected button for signal to reset the motion detector and control an LED whose rate of blinking indicates the status of the system.

The audio to play should be a WAV file (default is soundsource.wav- developed for a creepy motion-triggered elf-on-the-shelf, audio effects courtesy of the "ghost" filter at [https://voicechanger.io/](https://voicechanger.io/))


### Button Controls
<table>
  <tbody>
    <tr>
      <th align="center">Button Press Time</th>
      <th align="left">Purpose</th>
    </tr>
    <tr>
      <td align="center">0.5 sec</td>
      <td>Reset/reactivate system so it will wait for initial activation period (default 2 minutes) and then activate</td>
    </tr>
    <tr>
      <td align="center">3 sec</td>
      <td>Deactivate system (device is on but will not play audio when motion is detected)</td>
    </tr>
    <tr>
      <td align="center">6 sec</td>
      <td>Power off Raspberry Pi</td>
    </tr>
  </tbody>
</table>


### LED Blink Patterns
<table>
  <tbody>
    <tr>
      <th align="center">Blink Rate</th>
      <th align="left">Meaning</th>
    </tr>
    <tr>
      <td align="center">5 Hz</td>
      <td>System is in the initial activation period (default 2 minutes) and will soon activate</td>
    </tr>
    <tr>
      <td align="center">1 Hz</td>
      <td>System is active</td>
    </tr>
    <tr>
      <td align="center">0.5 Hz</td>
      <td>System is in a delay period after being previously activated</td>
    </tr>
    <tr>
      <td align="center">Off</td>
      <td>System is deactivated (Raspberry Pi may still be on and program may still be running)</td>
    </tr>
  </tbody>
</table>
