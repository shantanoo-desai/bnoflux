from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()


setup(name='bnoflux',
    version=1.2,
    description='Extract IMU Values from BNO055 and store them in InfluxDB via UDP',
    long_description=readme(),
    url='https://github.com/shantanoo-desai/bnoflux',
    author='Shantanoo Desai',
    author_email='shantanoo.desai@gmail.com',
    license='MIT',
    packages=['bnoflux'],
    scripts=[
        'bin/bnoflux',
        'bin/calibrate'
    ],
    install_requires=[
        'influxdb'
    ],
    include_data_package=True,
    zip_safe=False
)