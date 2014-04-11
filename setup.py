from setuptools import setup, find_packages
import os

setup(
    package_dir={'yubikey_totp_gui': './src'},
    packages=['yubikey_totp_gui'],
    name='yubikey-totp-gui',
    version='0.1',
    author_email='luke@lukedrummond.net',
    url='https://github.com/ldrumm/yubikey-totp-gui',
    author='Luke Drummond',
    long_description=open('README').read(),
    license = "2 clause BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=['python-yubico',],
    entry_points = {
        'console_scripts': [
            'yubikey-totp-gui = yubikey_totp_gui:main'
        ]
    },
)
