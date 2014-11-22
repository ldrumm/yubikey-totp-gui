yubikey-totp-gui
================

GUI for TOTP with the YubiKey.
Suitable for Two-Factor authentication with Gmail, Dropbox, Github, AWS etc.

Installation
============

Installation with `pip` should be fairly straightforward, but `pyusb` may not 
install cleanly as pip will refuse beta software by default. 
You will likely need to install the beta version first:

For the stable version:

    ``pip install pyusb==1.0.0b1 yubikey-totp-gui``

For the development version:

    ``pip install pyusb==1.0.0b1 git+https://github.com/ldrumm/yubikey-totp-gui.git``

Linux
=====

First, you will need Tkinter installed.

Debian and derivates:
    
    ``sudo apt-get install python-tk``

Chances are high that Tkinter will already be installed on everything but a 
freshly installed OS.

Permissions Issues
------------------
Some Linux distributions forbid direct access to USB devices, and require 
modification of system permissions. The simplest way to do this is to install
your distribution's packaged version of `yubikey-personalization` which takes
care of things for you, or alternatively copy the yubico udev rules:

    ``sudo curl -o /etc/udev/rules.d/69-yubikey.rules https://raw.githubusercontent.com/Yubico/yubikey-personalization/master/69-yubikey.rules``
    
    ``sudo curl -o /etc/udev/rules.d/70-yubikey.rules https://raw.githubusercontent.com/Yubico/yubikey-personalization/master/70-yubikey.rules``
    
    ``sudo service udev restart``

Windows
=======

Installation on windows currently has some issues, as python-yubico does not
seem to import properly (on my Windows 7 development machine at least). 
However, as Yubico `already offer a windows tool<https://www.yubico.com/applications/internet-services/gmail/>`_
that does essentially the same thing as this project, that software can be used 
as an alternative.

Other OSs
=========

I haven't had the opportunity to try this, but if your system has a libusb backend
and is somewhat unixy, it is likely to work just fine.

