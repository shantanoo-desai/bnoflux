# bnoflux

Python 3.x Command Line Utility for saving IMU information from [Bosch BNO055]() into InfluxDB via UDP and publishing data points to an MQTT broker

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

        usage: bnoflux [-h] --config CONFIG
        CLI for acquiring BNO055 values and toring it in InfluxDB and publishing via
        MQTT

        optional arguments:
        -h, --help       show this help message and exit
        --config CONFIG  Configuration conf.json file with path.

e.g.

    bnoflux --config /path/to/conf.json


## InfluxDB Settings

In the `influxdb.conf` add the `[[udp]]` table as follows:

```toml

[[udp]]
  enabled = true
  bind-address = ":8095"
  database = "BNO"
  precision = "n"
```

Make sure to match the udp port in `conf.json`.