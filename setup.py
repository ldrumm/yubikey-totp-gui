from setuptools import setup, find_packages
import os

setup(
    package_dir={'': 'src'},
    packages=[],
    name='yubikey-totp-gui',
    version='0.1',
    author_email='luke@lukedrummond.net',
    url='https://github.com/ldrumm/yubikey-totp-gui',
    author='Luke Drummond',
    long_description="""Simple TOTP for Yubikey.  Allows easy two-factor authentication for gmail, Dropbox, AWS and similar.""",
    license = "2 clause BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=['yubico'],
    entry_points = {
        'console_scripts': [
            'yubikey-totp-gui = yubikey_totp_gui:main'
        ]
    },
)
