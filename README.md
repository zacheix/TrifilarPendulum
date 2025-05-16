# TrifilarPendulum
Code created by Zachary Eix for finding the MOI of an object using a trifilar pendulum setup.

# Initial Info

Using this code assumes 3 conditions:
1. Your IMU is WitMotion WTGAHRS3.
2. Your Tension Cells are connected using a Phidgets Bridge.
3. Your GPIO pins output to a hex inverter for 5V step-up.

Throughout the code, there are various pin and serial definitions. The Phidgets bridge also has a defined serial number. Please change these definitions according to your setup.

# How the system was setup

Parts:
* IMU: WTGAHRS3
* Tension Cells: S-Type Load Cell - 100kg (C2) (Phidgets ID: 3138_0)
* Phidgets Bridge: PhidgetBridge 4-Input (Phidgets ID: 1046_1)
* Motor: YEJMKJ Nema 34 Stepper Motor 114MM 6A 1.8 degree step
* Motor Driver: DM860I
* Electromagnets: BDE-1716-12

As this is just a git repo, all other system specs can be requested.

# Script Specific Info
This system utilized 3 modular scripts. Each are named after M5, our projects name. **All scripts were run on a Linux driven RPi5.**

## *IMU.py*
The first script was for the IMU. This script reads data from the IMU, unpacks it, and scales to degrees. Due to the architecture of the system, we only return angle *Z*. This script will also intitially treat the fist reading as an offset, and 'zero' the further readings.

* Depending on serial connection, change serial port (*/dev/tty*)
* Depending on usage, change baud rate (*currently set to 230400*)

Libraries Needed:
* serial
* struct

## *M5Tension.py*
The second modular script is for the tension cells. Since we use 3 tension cells, this script attaches the 3 channels, and intializes them. The script reads data from the tension cells as Voltage Ratio, which is converted to kg in our main script.

Libraries Needed:
* Phidget22
 (*Please visit https://www.phidgets.com/docs/OS_-_Linux?srsltid=AfmBOor4jGpvGp00Qg8cuWXbAyg9jjAoB75IbUYm6qQ8G8_Mwg3KtQXe for installation instructions*)

## *M5GUI.py*
This is our main script, where a majority of everything is done. This script imports the 2 previous scripts for their data.

* Depending on chosen Phidget Bridge, change serial number. This is defined in '*measure_plate_mass*' and '*measure_object_mass*'

Constants:
* This script sets various constants. Please change as needed.
* For tension cell calibration, please see https://www.phidgets.com/docs/Calibrating_Load_Cells?srsltid=AfmBOooSio2F-2jYBSSciv8kFQ0wUq2ykdFnqiMFAebfutuicHoSav1R

Libraries Needed:
* numpy
* matplotlib
* PySimpleGUI
* scipy
* periphery

Notes:
* This script does calculate settling time, however during testing, we found that this calculation occasionally returns extreme numbers. Feel free to comment this line out (Ln 196).
* This script does return a plot for Time vs. ω, however depending on screen size, this plot may not show up properly.

# Further Documentation
* For ease of use and setup, this repo includes a PDFs, which is a code and systems analysis, which inlcudes a operation guide specific to our system.
* It is unlikely that I will further update these scripts, since they were made for a course project.
