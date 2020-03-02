#!/usr/bin/env python3
# Python3 Command Line Utility to Store BNO055 Values to InfluxDB via UDP
# and publish data points via MQTT
# Changes:
# - Add MQTT Publishing feature
# - Adapt the `measurement` dict to obtain line protocol strings
# - Linting
import os
import sys
import argparse
import logging
import time
import json
import concurrent.futures

from .BNO055 import BNO055
from influxdb import InfluxDBClient, line_protocol
from influxdb.client import InfluxDBClientError
import paho.mqtt.publish as publish

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

handler = logging.FileHandler("/var/log/bnoflux.log")
handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s-%(name)s-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

DEVICE = ''
sensor_bno = None
client = None
imu_conf = dict()
mqtt_conf = dict()


def publish_data(lineprotocol_data):
    """Publish IMU data points as line protocol strings to MQTT Broker"""
    lp_array = lineprotocol_data.split('\n')
    lp_array.pop()  # remove the last newline from the array
    publish_messages = []
    global imu_conf
    global mqtt_conf

    for topic in imu_conf['topics']:
        mqtt_msg = {
            'topic': DEVICE + '/' + topic,
            'payload': lp_array[imu_conf['topics'].index(topic)],
            'qos': 1,
            'retain': False
        }
        publish_messages.append(mqtt_msg)
    try:
        publish.multiple(
            publish_messages,
            hostname=mqtt_conf['broker'],
            port=mqtt_conf['port']
        )
        return True
    except Exception as mqtt_e:
        logger.error('MQTT publish Error: {e}'.format(e=mqtt_e))
        return False


def save_to_db(measurements):
    """Save Data to InfluxDB using UDP"""
    global client
    try:
        client.send_packet(measurements)
        return True
    except (Exception, InfluxDBClientError) as influx_e:
        logger.error('Error while UDP sending: {e}'.format(e=influx_e))
        return False


def read_from_imu(i2c_port, updaterate):
    logger.info('Starting to Read BNO values on {} every {}s'.format(i2c_port, updaterate))

    global sensor_bno
    sensor_bno = BNO055(i2c_bus_port=i2c_port)

    if sensor_bno.begin() is not True:
        raise ValueError('Initialization Failure for BNO055')
        sys.exit(1)
    time.sleep(1)
    sensor_bno.setExternalCrystalUse(True)
    time.sleep(2)
    measurement = {
        "tags": {
            "source": "imu"
        },
        "points": [
            {
                "measurement": "acceleration",
                "fields": {
                    "liX": -10000,
                    "liY": -10000,
                    "liZ": -10000
                }
            },
            {
                "measurement": "acceleration",
                "fields": {
                    "gX": -10000,
                    "gY": -10000,
                    "gZ": -10000
                }
            },
            {
                "measurement": "orientation",
                "fields": {
                    "yaw": -10000
                }
            },
            {
                "measurement": "orientation",
                "fields": {
                    "pitch": -10000
                }
            },
            {
                "measurement": "orientation",
                "fields": {
                    "roll": -10000
                }
            }
        ]
    }
    logger.info('reading sensor information')
    while True:
        try:
            timestamp = int(time.time() * 1e9)
            lx, ly, lz = sensor_bno.getVector(BNO055.VECTOR_LINEARACCEL)
            measurement['points'][0]['fields']['liX'] = lx
            measurement['points'][0]['fields']['liY'] = ly
            measurement['points'][0]['fields']['liZ'] = lz
            logger.debug('linear acc.: x:{}, y:{}, z:{}'.format(lx, ly, lz))

            gX, gY, gZ = sensor_bno.getVector(BNO055.VECTOR_GRAVITY)
            measurement['points'][1]['fields']['gX'] = gX
            measurement['points'][1]['fields']['gY'] = gY
            measurement['points'][1]['fields']['gZ'] = gZ
            logger.debug('gravity: x:{}, y:{}, z:{}'.format(gX, gY, gZ))

            yaw, roll, pitch = sensor_bno.getVector(BNO055.VECTOR_EULER)
            measurement['points'][2]['fields']['yaw'] = yaw
            measurement['points'][3]['fields']['pitch'] = pitch
            measurement['points'][4]['fields']['roll'] = roll
            logger.debug('euler: yaw:{}, pitch:{}, roll:{}'.format(yaw, pitch, roll))

            for point in measurement['points']:
                # insert timestamp to each point
                point['time'] = timestamp

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                if executor.submit(save_to_db, measurement).result():
                    logger.info('saved data to InfluxDB')
                if executor.submit(publish_data, line_protocol.make_lines(measurement, precision='ns')).result():
                    logger.info('published data to MQTT broker')
                time.sleep(updaterate)
        except Exception as imu_e:
            logger.error('Error while reading IMU data: {}'.format(imu_e))
            client.close()
            sys.exit(2)


def file_path(path_to_file):
    """Check if Path and File exist for Configuration"""

    if os.path.exists(path_to_file):
        if os.path.isfile(path_to_file):
            logger.info('File Exists')
            with open(path_to_file) as conf_file:
                return json.load(conf_file)
        else:
            logger.error('Configuration File Not Found')
            raise FileNotFoundError(path_to_file)
    else:
        logger.error('Path to Configuration File Not Found')
        raise NotADirectoryError(path_to_file)


def parse_args():
    """Pass Arguments for Configuration File"""

    parser = argparse.ArgumentParser(description='CLI for acquiring BNO055 values and toring it in InfluxDB and publishing via MQTT')
    parser.add_argument('--config', type=str, required=True, help='Configuration conf.json file with path.')

    return parser.parse_args()


def main():
    args = parse_args()
    CONF = file_path(args.config)
    global imu_conf
    imu_conf = CONF['imu']
    influx_conf = CONF['influx']

    global mqtt_conf
    mqtt_conf = CONF['mqtt']

    global DEVICE
    DEVICE = CONF['deviceID']

    logger.info('Creating InfluxDB Client')
    logger.debug('Client for {influx_host}@{influx_port} with udp:{udp_port}'.format(
        influx_host=influx_conf['host'],
        influx_port=influx_conf['port'],
        udp_port=imu_conf['udp_port']
    ))
    global client
    client = InfluxDBClient(
        host=influx_conf['host'],
        port=influx_conf['port'],
        use_udp=True,
        udp_port=imu_conf['udp_port']
    )
    logger.info('Checking Connectivity for InfluxDB')
    try:
        if client.ping():
            logger.info('Connected to InfluxDB')
        else:
            logger.info('Cannot Connect to InfluxDB. Check Configuration/Connectivity')
    except Exception as connection_e:
        logger.error(connection_e)
        client.close()
        sys.exit(1)

    logger.info('Connecting to IMU (BNO055) Device')
    logger.debug('Device @i2c-{port} with update rate={upd}'.format(
        port=imu_conf['i2cPort'],
        upd=imu_conf['updaterate']
    ))
    try:
        read_from_imu(
            i2c_port=imu_conf['i2cPort'],
            updaterate=imu_conf['updaterate'])
    except KeyboardInterrupt:
        print('CTRL+C hit for script')
        client.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
