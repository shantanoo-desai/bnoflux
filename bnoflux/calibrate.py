import sys
import time
import argparse

from .BNO055 import BNO055

sensor_bno = None


def calibrate(i2c_port):
    global sensor_bno
    sensor_bno = BNO055(i2c_bus_port=i2c_port)

    if sensor_bno.begin() is not True:
        raise ValueError('Sensor Initialization Failed')
        sys.exit(1)
    time.sleep(1)
    sensor_bno.setExternalCrystalUse(True)
    
    while not sensor_bno.isFullyCalibrated():
        print('Begin Calibration')
        time.sleep(0.1)
    
    print('Sensor Calibrated')
    new_calibration = sensor_bno.getCalibration()
    print('New Calibration Values: {}'.format(new_calibration))
    time.sleep(2)
    try:
        sensor_bno.setCalibration(new_calibration)
        print('Sensor Fully Calibrated and Values set.')
    except Exception as e:
        raise(e)
    time.sleep(0.5)


def parse_args():

    parser = argparse.ArgumentParser(description='Calibration Script for BNO055')

    parser.add_argument('--i2c-bus', type=int, required=False, default=0,
                        help='Provide the Number of the I2C port. E.g. for i2c0 -> 0, i2c -> 1')
    
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        calibrate(i2c_port=args.i2c_bus)
    except KeyboardInterrupt:
        print('Exiting Script')
        sys.exit(0)
    except Exception as e:
        raise(e)
        sys.exit(1)


if __name__ == "__main__":
    main()


