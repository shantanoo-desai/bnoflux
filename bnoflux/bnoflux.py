import sys
import argparse
import logging
import time
import json

from .BNO055 import BNO055
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

handler = logging.FileHandler("/var/log/bnoflux.log")
handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s-%(name)s-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

CONF_PATH = '/etc/umg/conf.json'
sensor_bno = None
client = None

def write_to_influx(db_client, data_points):
    _packet = {'points': data_points, 'tags': {'node': 'BNO055'}}
    logger.debug('Packet to Send: {}'.format(_packet))
    try:
        db_client.send_packet(_packet)
        logger.info('UDP Packet Sent')
    except InfluxDBClientError as e:
        db_client.close()
        raise(e)

def send_data(i2c_port, updaterate, db_host, db_port, udp_port):
    logger.info('Starting to Read BNO values on {} every {}s'.format(i2c_port, updaterate))
    try:
        global sensor_bno
        sensor_bno = BNO055(i2c_bus_port=i2c_port)
        
        if sensor_bno.begin() is not True:
            raise ValueError('Initialization Failure for BNO055')
            sys.exit(1)
        time.sleep(1)
        sensor_bno.setExternalCrystalUse(True)
        time.sleep(2)

        global client
        logger.info('Creating InfluxDB Connection')
        try:
            client = InfluxDBClient(host=db_host, port=db_port, use_udp=True, udp_port=udp_port)
        except InfluxDBClientError as e:
            logger.exception('Exception during InfluxDB Client Creation')
            client.close()
            raise(e)            
        logger.info('reading sensor information')
        while True:
            data_set = {
                'measurement': 'imu', 
                'fields':{
                    'yaw': -10000, 
                    'pitch': -10000, 
                    'roll': -10000,
                    'laX': -10000,
                    'laY': -10000,
                    'laZ': -10000,
                    'gX': -10000,
                    'gY': -10000,
                    'gZ': -10000,
                    'status': 0
                    }
            }
            yaw, roll, pitch = sensor_bno.getVector(BNO055.VECTOR_EULER)
            data_set['fields']['yaw'] = yaw
            data_set['fields']['roll'] = roll
            data_set['fields']['pitch'] = pitch
            
            lx, ly, lz = sensor_bno.getVector(BNO055.VECTOR_LINEARACCEL)
            data_set['fields']['laX'] = lx
            data_set['fields']['laY'] = ly
            data_set['fields']['laZ'] = lz

            gX, gY, gZ = sensor_bno.getVector(BNO055.VECTOR_GRAVITY)
            data_set['fields']['gX'] = gX
            data_set['fields']['gY'] = gY
            data_set['fields']['gZ'] = gZ

            logger.debug('Data Point: {}'.format(data_set))
            write_to_influx(client, [data_set])
    except Exception as e:
        logger.exception('Exception within `send_data` function')
        client.close()
        raise(e)



def parse_args():
    """Pass Arguments"""

    parser = argparse.ArgumentParser(description='CLI for acquiring BNO055 values and storing it in InfluxDB')

    parser.add_argument('--i2c-bus', type=int, required=False, default=0,
                        help='Provide the Number of the I2C port. E.g. for i2c0 -> 0, i2c -> 1')

    parser.add_argument('--updaterate', type=int, required=False, default=0.01, help='Update Rate for BNo Module in s. Default: 0.01s')    

    parser.add_argument('--udp-port', type=int, required=True, default=8095,
                        help='UDP Port for sending information via UDP.\n Should also be configured in InfluxDB')

    parser.add_argument('--db-host', type=str, required=False, default='localhost',
                        help='hostname for InfluxDB HTTP Instance. Default: localhost')

    parser.add_argument('--db-port', type=int, required=False, default=8086,
                        help='port number for InfluxDB HTTP Instance. Default: 8086')
    
    return parser.parse_args()


def main():
    args = parse_args()
    CONF = dict()

    if len(sys.argv) == 1:
        logger.info('Starting Script in Default Mode')
        # minimum configuration file
        logger.debug('CONF FILE: %s' % CONF_PATH)
        with open(CONF_PATH) as cFile:
            _conf = json.load(cFile)
            CONF = _conf['BNO055'] #store conf for BNO
            logger.debug('CONF: ' + json.dumps(CONF))
        try:
            send_data(i2c_port=CONF['i2cPort'],
                    updaterate=CONF['updaterate'],
                    db_host=args.db_host,
                    db_port=args.db_port,
                    udp_port=CONF['dbConf']['udp_port'])
        except KeyboardInterrupt:
            logger.exception('CTRL+C Hit')
            client.close()
            sys.exit(0)

    if len(sys.argv) > 1:
        if args.i2c_bus is None:
            print('Using I2C0 since nothing provided')
        if args.udp_port is None:
            print('provide UDP Port for InfluxDB')
            sys.exit(1)
        else:
            try:
                send_data(i2c_port=args.i2c_bus,
                        updaterate=args.updaterate,
                        db_host=args.db_host,
                        db_port=args.db_port,
                        udp_port=args.udp_port)
            except KeyboardInterrupt:
                logger.exception('CTRL+C Hit')
                client.close()
                sys.exit(0)

if __name__ == "__main__":
    main()
