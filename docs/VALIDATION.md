# Executed validation — 2026-10-23

Environment: Windows build **26200**, x64; Python **3.13.12**; Qt/PySide6
**6.8.3**; PyInstaller **6.22.3**. The primary display was reported as 3840 × 2160
physical pixels with a 3840 × 2088 usable region at **150%** scale. The machine
has 24 logical processors. No claim is made that other Windows builds were tested.

## Automated checks that passed

| Check | Result |
| --- | --- |
| `python -m pytest -q` | **56 passed** (latest unit run: 0.47 s) |
| Milestone A native marker probe | Opaque then alpha frames submitted; validated WorkerW child; no foreground change during the bounded probe |
| `scripts/smoke_windows.py` | 12 lifecycle checks passed; no errors |
| Native tray mode changes | Front → hidden → front → desktop; style/parent checks and persisted selection passed |
| Missing desktop host | Real child destroyed before simulated discovery failure; safe child recreated after restoring discovery |
| Pause during flight | Settled with branch; animation and pointer timers stopped |
| Quit | Drawing window and timers destroyed |
| `scripts/build_windows.ps1` | Tests, icon, x64 GUI executable, manifest and license packaging completed |
| Executable PE headers | AMD64 machine `0x8664`, GUI subsystem `2` |
| Packaged 25-second run | Autonomous perched → takeoff → flying → landing → perched cycle; safe native child at exit |
| Duplicate packaged launch | Second process exited without creating another runtime/report |
| Packaged hidden mode | Zero rendered frames and no drawing surface |
| Packaged front mode | Separate native topmost/pass-through/no-activate surface; 32 frames during the three-second check |
| Packaged paused mode | One static frame during the three-second check |
| `scripts/probe_front_hit.py` | A native hit-test at an opaque head/eye pixel passed to **another process**, while the front window was visible and had topmost/no-activate styles |

The native lifecycle smoke also checked interaction toggle persistence and that
the pet had no active window. Explorer was **not actually restarted**; recovery
was tested by making discovery temporarily return no windows. The native hit
probe queried `WindowFromPoint` without moving the pointer or sending a click.

## Measured resource use

The packaged autonomous run measured **55.19 MiB** working set and about
**0.177% whole-machine CPU** (4.246% of one logical processor) over 25.024 seconds.
Front mode measured 51.69 MiB / 0.108% whole-machine CPU over three seconds.
Paused mode drew once and measured 53.88 MiB / 0.021%; hidden mode drew zero
frames. These are short measurements on this machine, not performance guarantees.
The autonomous smoke used a 10-second rest setting to reach a complete cycle;
the shipped default remains 20–55 seconds.

Raw pointer-free evidence is included beside this file:

- `native-smoke.json`
- `bundle-smoke.json`
- `front-hit.json`

## Remaining manual acceptance

The full README acceptance checklists remain **not yet verified manually**.
In particular, native API/style/hit checks do not establish the visible desktop
compositor result, real icon opening/drag-selection/context-menu clicks, typing
and scrolling under the front pet, actual Explorer restart, reboot, fullscreen
behavior, physical DPI/primary-monitor changes, or Windows 10 compatibility.
The renderer's output was visually inspected as an offscreen artwork image;
that is not a desktop composition screenshot.

## Requirement update

After the original desktop-only implementation, the user requested selectable
front-of-apps and hidden modes. These are implemented explicitly and persisted.
See `REQUIREMENTS_UPDATE.md`. Desktop-host failure still never selects front
mode automatically. The original specification's desktop-only checklist now
applies specifically to desktop mode.
