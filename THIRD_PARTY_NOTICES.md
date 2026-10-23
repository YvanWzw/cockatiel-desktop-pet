# Third-party notices

The cockatiel and branch are original QPainter artwork implemented in this project.

The Windows bundle contains dynamically loaded Python and Qt for Python libraries.
PySide6 Essentials and Shiboken6 are provided by The Qt Company under their wheel's
applicable LGPL/GPL/commercial terms. Python is provided under the PSF license.
PyInstaller's bootloader is distributed under the GPL with its bootloader exception.
Dependency license texts shipped in their wheels and the upstream Qt 6.8.3
license texts are copied into `licenses/` by the packaging script. The PSF
license text is explicitly collected from the build interpreter.

Qt remains dynamically linked as separate DLLs under `_internal/`; retain these
files with the executable. The complete application source and build scripts
are supplied alongside the bundle. No external character artwork, sound,
network service, telemetry SDK, or downloaded runtime content is used.

Upstream projects and corresponding source/releases:

- https://www.qt.io/qt-for-python and https://code.qt.io/cgit/pyside/pyside-setup.git/ (6.8.3)
- https://www.python.org/downloads/source/
- https://github.com/pyinstaller/pyinstaller (6.22.3 for the supplied build)

See `licenses/` in the built application directory for the exact included texts.
