#!/usr/bin/env python
"""

Copyright (c) 2014, ldrumm. Contains portions from 'python-yubico-tools',
(c) 2011, 2012 Yubico AB.
All rights of the respective authors reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import sys
import time
import struct
import yubico
import webbrowser

from Tkinter import (
    Tk,
    Toplevel,
    IntVar,
    StringVar,
    Entry,
    Label,
    Menu,
    Button,
    Radiobutton,
    Frame,
    Checkbutton,
)
from gettext import gettext as _ #TODO
import tkMessageBox

__all__ = ['MainWindow']

DEFAULT_SLOT = 2
DEFAULT_TIME = 0
DEFAULT_STEP = 30
DEFAULT_DIGITS = 6

def _rzfill(string, to_len):
    """right-pad a string with zeros to the given length"""
    if len(string) > to_len:
        raise ValueError("string is already longer than to_len")
    return string + '0' * (to_len - len(string))

def _base32_to_hex(base32):
    """simple base conversion using the RFC4648 base32 alphabet"""
    ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    x = 0
    for digit in str(base32.upper().strip(' ')):
        x = x * len(ALPHABET) + ALPHABET.index(digit)
    return hex(x).lstrip('0x').rstrip('L').upper()


class _Credits(object):
    """This class spawns the dialogue to show the license information"""
    def __init__(self, parent):
        self.parent = parent
        top = self.top = Toplevel(parent.root)
        Label(top, text=__doc__).grid(columnspan=4)


class _ProgrammingWindow(object):
    """
    This class spawns the dialogue to configure programming the
    YubiKey with a base32 key for challenge-response SHA1 in either slot.
    """
    def __init__(self, parent):
        self.parent = parent
        top = self.top = Toplevel(parent.root)

        Label(top, text="Secret Key(base32):").grid(columnspan=3)

        base32_key = Entry(top)
        base32_key.grid(row=1, column=0, columnspan=3)

        challenge_response_slot = IntVar()
        challenge_response_slot_widgets = (
            Radiobutton(
                top,
                text='slot 1',
                variable=challenge_response_slot,
                value=1,
            ).grid(row=3, column=0),
            Radiobutton(
                top,
                text='slot 2',
                variable=challenge_response_slot,
                value=2,
            ).grid(row=3, column=1),
        )

        require_button = IntVar()
        require_button_widget = Checkbutton(top,
                text='Button press required',
                variable=require_button,
            ).grid(row=2, columnspan=3)
        require_button.set(1)

        submit = Button(top,
            text="Program",
            command=lambda: self._program_confirm(
                challenge_response_slot.get(),
                base32_key.get(),
                require_button.get()
            )
        ).grid(row=4, column=1)

        cancel = Button(
            top,
            text="Cancel",
            command=self._program_cancel
        ).grid(row=4, column=0)

    def _program_cancel(self):
        """guess pylint"""
        self.top.destroy()

    def _program_confirm(self, slot, base32_key, require_button):
        """Confirms that programming should take place"""
        #print base32_key
        if slot != 1 and slot != 2:
            return tkMessageBox.showerror("Error", "Please Choose a slot")

        if tkMessageBox.askokcancel("Confirm",
            """Overwrite slot %s?\n"""
            """This cannot be undone, and is presently experimental\n"""
            """with the possibility of setting fire to your YubiKey""" % slot):
            self._program_key(slot, base32_key, require_button)
        else:
            self._program_cancel()

    def _program_key(self, slot, base32_key, require_button):
        """Once we get here, things get destructive"""
        config = self.parent.yk.init_config()
        config.extended_flag('SERIAL_API_VISIBLE', True)
        print require_button
        config.mode_challenge_response(
            'h:' + _rzfill(_base32_to_hex(base32_key), 40),
            type='HMAC',
            variable=True,
            require_button=bool(require_button),
        )
        try:
            self.parent.yk.write_config(config, slot=slot)
            tkMessageBox.showinfo("Success", "Successfully programmed YubiKey in slot %s." % slot)
        except (yubico.yubico_exception.YubicoError, yubico.yubico_exception.InputError) as e:
            tkMessageBox.showerror("Error", e)
        self._program_cancel()


class MainWindow(object):
    """Yubkey TOTP Challenge response root window
    Contains options for fetching a TOTP from the Yubikey

    """
    def __init__(self, root):

        self.key_dialogue = {}
        self.root = root
        self.frame = Frame(root)
        self.frame.grid()
        self._menu_setup()

        self.version = StringVar()
        self.version_widget = Label(
            self.frame,
            textvariable=self.version
        ).grid(column=0, row=2)

        self.serial = StringVar()
        self.serial_widget = Label(
            self.frame,
            textvariable=self.serial
        ).grid(column=1, row=2,)

        self.yk = None
        self.detect_yubikey()

        self.slot = IntVar()
        self.slot.set(DEFAULT_SLOT)
        self.base32_key = StringVar()
        self.digits = IntVar()
        self.digits.set(DEFAULT_DIGITS)

        self.totp = Button(
            self.frame,
            text="Get TOTP",
            command=self.get_totp
        ).grid(column=0, row=0)

        self.challenge_response_slot = (
            Radiobutton(text='slot 1',
                variable=self.slot,
                value=1,
            ).grid(row=2, column=0),
            Radiobutton(text='slot 2',
                variable=self.slot,
                value=2,
            ).grid(row=2, column=1)
        )

        self.digits_radio = (
            Radiobutton(text='6 digits',
                variable=self.digits,
                value=6,
            ).grid(row=3, column=0),
            Radiobutton(text='8 digits',
                variable=self.digits,
                value=8,
            ).grid(row=3, column=1)
        )
        
        self.user_message = StringVar()
        self.user_message.set(
            "Choose challenge-response\n"\
            "slot, then click 'Get OTP'"
        )
        self.message_widget = Label(
            self.frame,
            textvariable=self.user_message
        ).grid(column=1, row=0, columnspan=2)

    def _menu_setup(self):
        """Pull-down menus init"""
        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Quit", command=self.frame.quit)

        edit_menu = Menu(menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Program YubiKey for TOTP...", command=self._program_key)

        help_menu = Menu(menu)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="HowTo...", command=self._help_dialogue)
        help_menu.add_command(label="About...", command=self._about_dialogue)
        help_menu.add_command(label="Credits...", command=self._credits_dialogue)

    def _help_dialogue(self):
        """callback for the help->help pulldown"""
        webbrowser.open('https://www.yubico.com/applications/internet-services/gmail/')

    def _about_dialogue(self):
        """callback for the help->about pulldown"""
        webbrowser.open('https://github.com/ldrumm/yubikey-totp-gui')

    def _credits_dialogue(self):
        """callback for the help->about pulldown"""
        credits_dialogue = _Credits(self)
        self.root.wait_window(credits_dialogue.top)

    def _program_key(self):
        """
        callback for the edit->Program YubiKey pulldown
        Opens a new configuration window, blocking until exit.
        """
        prg_dialogue = _ProgrammingWindow(self)
        self.root.wait_window(prg_dialogue.top)

    def detect_yubikey(self):
        """Tries to detect a plugged-in YubiKey else alerts user"""
        try:
            self.yk = yubico.find_yubikey()
            self.version.set("Version:%s" % self.yk.version())
            self.serial.set("Serial:%s" % self.yk.serial())
#            except (yubico.yubico_exception.YubicoError, yubico.yubikey_usb_hid.usb.USBError):
        except Exception:
            self.version.set("No YubiKey detected")
            self.serial.set("")
            self.yk = None

    def _make_totp(self):
        """
        Create an OATH TOTP OTP and return it as a string (to disambiguate leading zeros).
        This is ripped straight out of yubico's command-line script, `yubikey-totp`.
        Credit due.
        """
        secret = struct.pack('> Q', int(time.mktime(time.gmtime())) / DEFAULT_STEP).ljust(64, chr(0x0))
        response = self.yk.challenge_response(secret, slot=self.slot.get())
        # format with appropriate number of leading zeros
        fmt = '%.' + str(self.digits.get()) + 'i'
        totp_str = fmt % (yubico.yubico_util.hotp_truncate(response, length=self.digits.get()))
        return totp_str

    def get_totp(self):
        otp = None
        self.detect_yubikey()
        if self.yk is None:
            return
        self.user_message.set("Touch the yubikey button")
        try:
            otp = self._make_totp()
        except yubico.yubico_exception.YubicoError as e:
            self.user_message.set(e)
            return
        if not otp:
            self.user_message.set("No TOTP received from YubiKey")
        self.root.clipboard_clear()
        self.root.clipboard_append(otp)
        self.user_message.set("%s\ncopied to clipboard" % otp)

def main():
    root = Tk()
    root.wm_title('Yubikey-TOTP')
    MainWindow(root)
    return root.mainloop()

if __name__ == '__main__':
    sys.exit(main())


