# bnoflux

Python 3.x Command Line Utility for saving IMU information from [Bosch BNO055]() into InfluxDB via UDP

## Installation and Development

### Installation

Initially install `python-smbus` using:

    apt-get install python-smbus

clone repository to your machine and use `pip` to install the CLI:

    pip install .

### Development

develop using `venv` as follows:

    python -m venv venv

activate the virtual environment, install using:

    pip install -e .


## Usage

1. Calibration. (default I2C Port if not provided is 0)

        usage: calibrate [-h] [--i2c-bus I2C_BUS]

        Calibration Script for BNO055

        optional arguments:
        -h, --help         show this help message and exit
        --i2c-bus I2C_BUS  Provide the Number of the I2C port. E.g. for i2c0 -> 0,
                            i2c -> 1

2. Storage. (default I2C Port if not provides is 0)

        usage: bnoflux [-h] [--i2c-bus I2C_BUS] [--updaterate UPDATERATE] --udp-port
               UDP_PORT [--db-host DB_HOST] [--db-port DB_PORT]

        CLI for acquiring BNO055 values and storing it in InfluxDB

        optional arguments:
        -h, --help            show this help message and exit
        --i2c-bus I2C_BUS     Provide the Number of the I2C port. E.g. for i2c0 ->
                                0, i2c -> 1
        --updaterate UPDATERATE
                                Update Rate for BNo Module in s. Default: 0.01s
        --udp-port UDP_PORT   UDP Port for sending information via UDP. Should also
                                be configured in InfluxDB
        --db-host DB_HOST     hostname for InfluxDB HTTP Instance. Default:
                                localhost
        --db-port DB_PORT     port number for InfluxDB HTTP Instance. Default: 8086