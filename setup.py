import os
import sys
import textwrap
import select
import platform

from setuptools import setup, find_packages
from setuptools.command.install import install as SetupToolsInstaller

import gettext
t = gettext.translation(
    'yubikey_totp_gui', 
    os.path.join(os.path.dirname(__file__), 'lang'),
    fallback=True
)
_ = t.ugettext


def timed_raw_input(timeout, prompt=""):
    sys.stderr.write(prompt + '\n') # pip seems to linebuffer the output somehow
    sys.stderr.flush()
    import time
    time.sleep(1)
    ready_fds = select.select([sys.stdin], [], [], timeout)
    if not len(ready_fds[0]):
        raise IOError("timeout waiting for user input")
    return sys.stdin.readline().strip('\n')


def write_files(os_rules):
    """
    For systems that use individual configuration files, use the 'files' permissions target
    and write the content of each file in the list into the first directory that
    exists.
    
    If the files already exist, we leave them alone.
    If none of the directories exist, we fail loudly.
    """
    dirs = os_rules['try_dirs']
    files = os_rules['files']
    for directory in dirs:
        try:
            os.stat(directory)
            break
        except OSError:
            continue
    else:
        raise ValueError(_("None of the expected installation directories were found"))

    for name in files:
        filepath = os.path.join(directory, name)
        try:
            os.stat(filepath)
            sys.stderr.write(
                _("'%(filepath)s' already exists. Skipping\n") % {'filepath': filepath}
            )
            continue
        except OSError:
            # OSError means the file doesn't yet exist.
            pass
        try:
            with open(filepath, 'w') as f:
                f.write(files[name])
                f.flush()
        except IOError:
            # need to retry with `sudo`
            import subprocess
            ps = subprocess.Popen(
                ['sudo', 'tee', filepath],
                stdin=subprocess.PIPE,
            )
            ps.stdin.write(files[name])
            ps.stdin.close()
            ps.wait()


USB_RULES = {
    'Linux': {
        'action': write_files,
        'try_dirs':['/etc/udev/rules.d', '/lib/udev/rules.d'],
        'files': {
            '69-yubikey.rules': textwrap.dedent(
                """
                ACTION!="add|change", GOTO="yubico_end"
                ATTRS{idVendor}=="1050", 
                ATTRS{idProduct}=="0010|0110|0111|0114|0116|0401|0403|0405|0407|0410", \\
                ENV{ID_SECURITY_TOKEN}="1"
                LABEL="yubico_end"
                """),
            '70-yubikey.rules': textwrap.dedent(
                """
                ACTION=="add|change", SUBSYSTEM=="usb", \\
                ATTRS{idVendor}=="1050", \\
                ATTRS{idProduct}=="0010|0110|0111|0114|0116|0401|0403|0405|0407|0410", \\
                TAG+="uaccess", TAG+="udev-acl"
                """),
        },
    },
#TODO 
#    'openbsd': {
#        'try_dirs': [],
#        'files': {
#        }
#    },
#    'freebsd': {
#        'action': append_conf,
#        'try_dirs': ['devd.conf'],
#        'blocks': [textwrap.dedent("""
#            attach 100 {
#            match "vendor" "1050";
#            match "product" "0010|0110|0111|0114|0116|0401|0403|0405|0407|0410"
#            action 
#        """)],
#};

#        }
#    },
}


class Installer(SetupToolsInstaller):
    """
    Override the standard setuptools installer to do some permissions-related
    extra business before exit.
    """
    
    def run(self):
        SetupToolsInstaller.run(self)
        if os.isatty(sys.stdin.fileno()):
            try:
                if timed_raw_input(30, _(
                    "Do you want to add the necessary USB permissions (as root)?\n"
                    "Will skip automatically in %(timeout)ss:[N/y]" % {'timeout': 30}
                )) in _('Yy'):
                    os_name = platform.system()
                    try:
                        func = USB_RULES[os_name]['action']
                    except KeyError:
                        sys.stderr.write("Your OS isn't yet supported. Please file a bug report")
                        sys.exit(False)
                    func(USB_RULES[os_name])
            except IOError:
                # timeout
                print _("skipping permissions installation...")

setup(
    cmdclass = {'install' : Installer},
    package_dir={'yubikey_totp_gui': './src'},
    packages=['yubikey_totp_gui'],
    name='yubikey-totp-gui',
    version='0.3',
    author_email='luke@lukedrummond.net',
    url='https://github.com/ldrumm/yubikey-totp-gui',
    author='Luke Drummond',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    license = "2 clause BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Security",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=['python-yubico', 'pyusb==1.0.0b2'],
    entry_points = {
        'console_scripts': [
            'yubikey-totp-gui = yubikey_totp_gui:main'
        ]
    },
)
