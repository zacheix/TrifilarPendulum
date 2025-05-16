import time
import serial
import struct
 
# Open serial port to the IMU
ser = serial.Serial("/dev/ttyUSB0", 230400, timeout=0.5)
 
def read_gyro_z():
    """
    Reads a single gyro Z-axis measurement from the IMU.
    This function waits until a valid packet is received,
    then unpacks and returns the scaled gyro Z angle in degrees.
    """
    while True:
        # Sync to header byte
        if ser.read(1) == b'\x55':
            data_type = ser.read(1)
            if data_type == b'\x53':  # Angle data packet
                data = ser.read(8)
                if len(data) == 8:
                    # Unpack as four signed 16-bit integers (pitch, roll, yaw, temp)
                    ax, ay, az, temp = struct.unpack('<hhhh', data)
                    return az / 32768.0 * 180  # Scale to degrees
 
def get_initial_offset():
    """
    Returns an initial gyro Z reading as the offset.
    """
    return read_gyro_z()
 
if __name__ == "__main__":
    # Only run the following code if this module is executed directly.
    # When imported, this block will not be executed.
    initial_offset = get_initial_offset()
    print(f"Initial Gyro Z Offset: {initial_offset:.2f}")
    # Continuously read gyro Z and print at a controlled rate.
    gyro_z_values = []  # Store gyro values for reference
    sampling_rate = 100  # Hz
    print_rate = 0.1     # Print rate (in seconds)
    try:
        start_time = time.time()
        while True:
            gyro_z = read_gyro_z() - initial_offset
            gyro_z_values.append(gyro_z)
            # Print every print_rate seconds
            if time.time() - start_time >= print_rate:
                print(f"Calibrated Z Angle: {gyro_z_values[-1]:.2f}")
                start_time = time.time()
            time.sleep(1 / sampling_rate)
    except KeyboardInterrupt:
        print("\nStopped by user.")
        ser.close()