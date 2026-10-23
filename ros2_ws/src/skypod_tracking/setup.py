from setuptools import setup, find_packages
from setuptools import find_packages, setup

package_name = 'skypod_tracking'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='skypod_developer',
    maintainer_email='developer@example.com',
    description='SkyPod target tracking and pan tilt simulation',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'target_simulator = skypod_tracking.target_simulator:main',
        'pan_tilt_controller = skypod_tracking.pan_tilt_controller:main',
        'udp_receiver = skypod_tracking.udp_receiver:main',
    ],
 },
)

