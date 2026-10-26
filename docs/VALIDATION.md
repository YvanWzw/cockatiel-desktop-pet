# Executed validation — 2026-10-26, version 1.1.0

Environment: Windows build **26200**, x64; Python **3.13.12**; Qt/PySide6
**6.8.3**; PyInstaller **6.22.3**. The primary display was reported as 3840 × 2160
physical pixels with a 3840 × 2088 usable region at **150%** scale. The machine
has 24 logical processors. No claim is made that other Windows builds were tested.

## Automated checks that passed

| Check | Result |
| --- | --- |
| `python -m pytest -q` | **63 passed** (latest unit run: 0.54 s) |
| Milestone A native marker probe (2026-10-23 baseline) | Opaque then alpha frames submitted; validated WorkerW child; no foreground change during the bounded probe |
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

The packaged autonomous run measured **75.66 MiB** working set and about
**0.109% whole-machine CPU** (2.619% of one logical processor) over 25.055 seconds.
Front mode measured 69.30 MiB / 0.086% whole-machine CPU over three seconds.
Paused mode drew once and measured 71.47 MiB / 0.064%; hidden mode drew zero
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
The 1.1 renderer's output was visually inspected as offscreen artwork images;
the accompanying GIF is exported directly from the runtime renderer. This is
not a desktop composition screenshot. The current package was checked to
contain the atlas PNG, anatomical metadata and asset provenance document.

Additional tests cover seeded quiet intervals, brief blinks, continuous wing
phases, bundled asset loading, feather opacity during blends and complete pose
replacement during grooming. Head tracking uses a stable neck pivot to avoid
double eyes/beaks. Wing articulation keeps the same torso/head image between
frames. Branch geometry remains independent of bird lift.

## Requirement update

After the original desktop-only implementation, the user requested selectable
front-of-apps and hidden modes. These are implemented explicitly and persisted.
See `REQUIREMENTS_UPDATE.md`. Desktop-host failure still never selects front
mode automatically. The original specification's desktop-only checklist now
applies specifically to desktop mode.

On 2026-10-26 the original vector bird was replaced by original feathered
artwork and a layered 2D animation rig after observing the user's NetEase Cloud
Music pet UI. No screenshots or proprietary character files were copied into
the project. See the updated requirement note and bundled artwork prompt record.
