# Cockatiel Desktop Pet — Codex Implementation Specification

**Document type:** Product requirements, architecture, and implementation plan  
**Target:** Windows 10/11 (x64), desktop application  
**Preferred stack:** Python 3.12+, PySide6 (Qt 6), Win32 APIs via `ctypes`  
**Primary deliverable:** A working, packaged desktop pet, not merely a design or demo

## 1. Objective

Build a lightweight desktop pet featuring a recognizable **cockatiel** (small parrot). The bird moves independently around the Windows desktop, flaps its wings, lands on a short tree branch, rests, blinks, and reacts to the mouse.

The defining constraint is **desktop-only behavior**:

- The bird may appear over the desktop wallpaper, ideally behind desktop icons.
- It **must never be drawn above ordinary application windows**, interfere with typing or clicking, or steal keyboard focus.
- It must not appear as an always-on-top overlay or become an intrusive floating window.
- If a safe desktop-hosting mechanism is unavailable, the bird must stay hidden and the application must notify the user through the system tray. **Do not silently fall back to a topmost or ordinary floating overlay.**

Implementation assumption: the user has not specified an operating system, so **Windows 10/11 is the MVP target**. Do not claim macOS or Linux support.

## 2. MVP Scope and Out of Scope

### Required for MVP

1. A small, attractive 2D cockatiel with transparent background and simple procedural animations.
2. Automatic periodic flying from one resting place to another.
3. A visible short branch beneath the cockatiel **only while landing/perched**.
4. Simple mouse responses: look toward nearby cursor, blink/head tilt on hover, and an optional chirp-like visual response when clicked. Clicks must still reach the desktop normally.
5. True desktop-level integration, with no interference with open windows, application focus, taskbar, or desktop icon interaction.
6. System tray controls: **Pause/Resume**, **Fly Now**, **Mouse Interaction On/Off**, **Quit**.
7. Config persistence, bounded CPU usage, reasonable idle behavior, and Explorer restart recovery.
8. A run command, Windows executable packaging instructions, automated unit tests, and a manual Windows smoke-test checklist.

### Not required for MVP

- Speech recognition, AI chat, feeding system, achievements, networking, analytics, advertisements, or account login.
- Complex skeletal animation, physics engines, or downloaded copyrighted character artwork.
- A settings dialog; a JSON config file and tray actions are sufficient.
- Native support for macOS/Linux.
- Multi-monitor roaming; **primary-monitor support is mandatory**, multi-monitor flight is a later enhancement. Secondary monitors must not cause crashes or misplaced windows.
- Audio: optional and **off by default**. All required interactions must work silently.

## 3. User Experience and Art Direction

### Appearance

Use an original, cute, readable 2D illustration. Generate the cockatiel artwork programmatically using `QPainter` paths/shapes so the project has no external art dependency.

The bird should be visually identifiable as a cockatiel:

- Soft gray body and wings, long pointed tail.
- Yellow head with a raised yellow crest.
- Bright orange cheek patches.
- Small dark eye and curved beak.
- Tiny feet that visibly grip a branch when perched.

Preferred proportions on a 1920 × 1080 display at 100% scale:

- Perched bird drawing: approximately **110–155 px tall**.
- Branch: approximately **165–230 px long**, 8–14 px thick, lightly tapered and organically curved.
- Transparent rendering surface: only large enough for the bird, wing movement, and branch, e.g. ~280 × 240 logical px before DPI scaling.
- Crisp antialiasing, subtle outlines, gentle easing; avoid very fast or flashing animation.

The branch is a visual landing prop, not a large tree. Draw it behind the feet and bird, with a main wooden curve and one or two small twigs. It should fade in as landing completes and fade out during takeoff.

### Motion and visual personality

- Resting: blink, small body sway/breathing, occasional crest movement and grooming.
- Takeoff: crouch, open wings, accelerate gradually; fade/remove branch as feet leave it.
- Flying: visible wing flaps, small vertical bob, slight body pitch, correct left/right orientation.
- Landing: decelerate, align feet with branch, fold wings, settle with slight bounce.
- Pointer nearby: bird turns head or tilts crest toward cursor.
- Pointer approaches rapidly: optional tiny hop/startle, with a cooldown so it is not constantly escaping.
- Passive click over bird while desktop is exposed: a quick blink, head tilt, or visual chirp; do not consume the click.

Do not teleport between destinations. No bird animation should cover dialogs, browsers, games, video players, or other app windows.

## 4. Non-Negotiable Behavior and Safety Invariants

Treat these as hard requirements, not optional polish.

1. **No topmost overlay:** never use `Qt.WindowStaysOnTopHint`, `HWND_TOPMOST`, or a persistent transparent full-screen top-level window to display the bird.
2. **Desktop hierarchy:** the visible drawing window must be hosted at a verified desktop shell layer behind normal applications. Prefer the desktop wallpaper/`WorkerW` area behind icons.
3. **No focus:** the pet must never activate itself, appear in Alt+Tab, or create a normal taskbar button.
4. **Mouse pass-through:** the bird and branch never receive or consume mouse messages; ordinary desktop clicks, dragging, icon selection, right-click context menus, and clicks into other programs work normally.
5. **Observe, do not intercept:** mouse interaction comes from passively polling cursor location/button state only. No low-level hooks, injected input, cursor warping, `SetCapture`, synthetic clicks, or global keyboard hooks.
6. **Graceful failure:** if Windows shell attachment fails, if the host disappears, or if layering is uncertain, hide/destroy the visual child window immediately. Keep only tray UI and attempt safe reconnection.
7. **No Explorer modification:** do not inject a DLL, subclass another process's window procedure, replace the wallpaper, or patch Explorer.
8. **No network/telemetry:** application runs fully locally and never records mouse positions or click history to disk.

If any requested visual effect conflicts with these invariants, favor **non-interference** over animation fidelity.

## 5. Technical Architecture

### Recommended stack

- **Python 3.12+** for behavior/state machine, config, and orchestration.
- **PySide6 / Qt 6** for the event loop, 2D `QPainter` drawing, timers, menu, and `QSystemTrayIcon`.
- **Win32 through `ctypes`** for shell-host discovery, native window parenting, layered mouse-transparent window styles, cursor polling, and HWND validation.
- **pytest** for unit tests.
- **PyInstaller** for a Windows executable (`--onedir --windowed` preferred).

Avoid Electron, a browser window, or a normal always-on-top Qt widget; those make the strict desktop-only requirement harder to guarantee.

### Components

| Component | Responsibility |
|---|---|
| `DesktopHost` | Find/validate the Windows desktop host; attach the drawing window; recover when Explorer restarts. |
| `PetSurface` | Maintain a small alpha-transparent, click-through native/Qt drawing surface. |
| `CockatielRenderer` | Draw bird, branch, wings, facial expressions, and simple procedural animation. |
| `PetController` | Deterministic state machine and transition timers. |
| `FlightPlanner` | Choose safe start/end locations and generate smooth flights. |
| `MouseObserver` | Passively sample pointer position, pointer speed, and button edges; gate reactions to desktop only. |
| `TrayController` | Pause/Resume, Fly Now, interaction toggle, Quit, error notification. |
| `ConfigStore` | Validate defaults and save/load JSON settings. |

Keep Win32 details isolated from behavior and rendering. The state machine and geometry must be testable without a running Windows Explorer process.

### Suggested repository structure

```text
cockatiel-desktop-pet/
├── pyproject.toml
├── README.md
├── COCKATIEL_DESKTOP_PET_SPEC.md
├── src/
│   └── cockatiel_pet/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── config.py
│       ├── models.py
│       ├── state_machine.py
│       ├── flight.py
│       ├── renderer.py
│       ├── pet_surface.py
│       ├── desktop_host.py
│       ├── mouse_observer.py
│       └── tray.py
├── tests/
│   ├── test_state_machine.py
│   ├── test_flight.py
│   ├── test_geometry.py
│   ├── test_interactions.py
│   └── test_config.py
└── scripts/
    └── build_windows.ps1
```

## 6. Windows Desktop Integration — Highest-Risk Milestone

**Implement and verify this before investing in animations.** Windows desktop host internals vary across Windows 10/11 builds. The widely used `Progman`/`WorkerW` technique relies partly on undocumented shell behavior, so finding an HWND is **not proof** that the bird is in the correct visible layer.

### 6.1 Host discovery

1. Discover the top-level `Progman` window (`FindWindowW`).
2. Enumerate top-level windows (`EnumWindows`) and their children (`FindWindowExW`/`EnumChildWindows`). Look for the desktop icon view `SHELLDLL_DefView` and related `WorkerW` windows. Do **not** assume one fixed window hierarchy.
3. If needed, request creation of a wallpaper worker with the **undocumented** `0x052C` message sent to `Progman` via `SendMessageTimeoutW` with a short timeout and `SMTO_ABORTIFHUNG`. Never block indefinitely or depend on the message always working.
4. Identify a candidate `WorkerW` desktop wallpaper host that is visually **behind desktop icons and below normal application windows**. Check class, non-null HWND, validity (`IsWindow`), screen geometry, and expected shell process ownership.
5. Create a small transparent pet window as a **child** of that host. When using `SetParent`, correctly manage `WS_CHILD` versus `WS_POPUP` styles, and call `SetWindowPos` with `SWP_NOACTIVATE` and frame-change flags when required.
6. Verify physical/Qt coordinates and per-monitor DPI behavior. Window positions must be transformed between desktop screen coordinates and host **client coordinates** (e.g. `ScreenToClient`) before moving a native child.
7. Validate on an actual Windows 10/11 desktop that the surface is visible, that icons are usable, and that opening a normal program covers the bird completely.

**Do not** attach the bird to `SHELLDLL_DefView` or the icon `SysListView32` in a way that breaks icon drawing or interactions. Do not use `SetParent(hwnd, NULL)` as a substitute for the wallpaper host.

### 6.2 Native window and rendering strategy

Preferred initial attempt:

- Build a small frameless `QWidget` with `WA_TranslucentBackground` and a QPainter-based `paintEvent`.
- Create/get its native HWND with `winId()` and embed it in the validated desktop host using Win32 `SetParent`, adjusting styles as specified in Win32 documentation.
- Apply `WS_EX_NOACTIVATE` and `WS_EX_TOOLWINDOW`, and ensure the visible window is mouse-transparent. `WS_EX_LAYERED | WS_EX_TRANSPARENT` may be used with a layered child (supported on Windows 8+). Preserve other pre-existing styles.
- Ensure Qt flags do not later recreate the HWND as a top-level window; handle `WinIdChange` or recreate/re-embed deliberately if necessary.
- Use a small moving viewport rather than a full-screen transparent window. Update QPainter animation in this small surface.

If Qt's window parenting/transparency combination is invisible or unstable on a specific Windows build, try an alternative **native Win32 layered child window** hosted by the validated shell HWND, using offscreen `QImage`/`QPainter` plus per-pixel-alpha `UpdateLayeredWindow`. Encapsulate this behind the same `PetSurface` interface. Do not switch to a regular floating overlay.

**Important implementation detail:** `WM_NCHITTEST` returning `HTTRANSPARENT` by itself is not a reliable cross-process click-through mechanism. Verify genuine pass-through with layered/transparent window styles and manual testing. Use the Win32 APIs with correct `ctypes` `argtypes`/`restype` for 64-bit HWNDs.

### 6.3 Recovery and fail-safe behavior

- Recheck shell HWND validity every **2–5 seconds** and when display topology changes.
- On Explorer restart or host HWND disappearance: hide and tear down the child drawing window before continuing; rediscover the host and rebuild the surface only after revalidation.
- If attachment fails, keep the app running in the system tray with a clear notification, such as: `Desktop host unavailable; pet is hidden to avoid covering applications.`
- Do not aggressively launch or restart Explorer, change the registry, or run elevated.
- Add a debug log of discovered window classes/handles and state transitions (no pointer trace). Include a switch such as `--debug-desktop-host` for diagnostics.

### 6.4 Desktop-only interaction gating

Use `GetCursorPos` to observe the pointer. Before a hover/click reaction, determine whether the pointer is currently on the visible Explorer desktop, e.g. inspect `WindowFromPoint`/root ancestry and known shell windows. Do **not** trigger interactions when the point belongs to another application, the taskbar, Start menu, an Explorer popup menu, or an unknown window.

A passive button-edge check may use the **high bit** of `GetAsyncKeyState(VK_LBUTTON)`; track rising edges locally. Handle left/right swapped buttons if practical. Polling must never consume or modify the click.

If desktop exposure cannot be determined confidently, **ignore the interaction** rather than responding to a click in another application.

## 7. Behavior State Machine

Use explicit states and seeded randomness. Drive transitions with real elapsed `dt` from a monotonic clock; clamp large `dt` values after resume.

| State | Visual | Default duration / exit |
|---|---|---|
| `PERCHED` | Branch visible; bird breathes, blinks, looks around, occasionally grooms. | Stay ~20–55 seconds, randomized. |
| `TAKEOFF` | Small crouch, wing spread, upward motion; branch fades out. | ~0.3–0.6 sec, then `FLYING`. |
| `FLYING` | Flapping, bobbing, turning along a smooth path. No branch. | ~2–8 sec, depending on route. |
| `LANDING` | Slow descent, wing fold, feet contact new branch; branch fades in. | ~0.4–0.8 sec, then `PERCHED`. |
| `REACTING` | Head tilt, blink, excited crest/visual chirp; branch still visible if perched. | ~0.4–1.2 sec, then `PERCHED`. |
| `PAUSED` | Static perched pose/branch; no autonomous movement, minimal repainting. | Until Resume. |

Behavior requirements:

- Start perched at a valid location with a visible branch.
- No repeated forced flights more often than once every ~10 sec. Manual **Fly Now** may override the regular timer.
- The bird must not immediately take off every time the cursor passes by.
- Flight endpoints are inside safe desktop display bounds with at least 30–50 px padding from edges and away from the taskbar.
- Keep bird/branch fully on the primary monitor, allowing transparent drawing margins.
- If the display shrinks or DPI changes, re-clamp coordinates rather than becoming unreachable.
- On Pause during flight, settle safely to a nearest valid perch or freeze/restart in a documented, stable manner; do not leave a branch floating disconnected from the feet.

### State transition pseudocode

```python
def update(dt: float, pointer: PointerSample) -> None:
    dt = min(dt, 0.05)  # prevent giant jumps after sleep/suspend
    if paused:
        return

    mouse_event = mouse_observer.classify(pointer)
    if state == PERCHED:
        update_idle_animation(dt)
        if mouse_event in {HOVER, DESKTOP_CLICK_ON_BIRD} and reaction_ready():
            enter(REACTING)
        elif idle_timer_elapsed():
            select_next_perch()
            enter(TAKEOFF)
    elif state == TAKEOFF and animation_complete():
        enter(FLYING)
    elif state == FLYING:
        position, heading = flight_path.sample(progress(dt))
        if flight_path.finished:
            enter(LANDING)
    elif state == LANDING and animation_complete():
        enter(PERCHED)
    elif state == REACTING and animation_complete():
        enter(PERCHED)
```

## 8. Flight and Perch Geometry

Use a smooth cubic Bézier curve or eased interpolation rather than linear constant-speed movement.

Suggested path:

```text
P0 = current perch / takeoff position
P3 = destination perch
P1 = P0 + horizontal displacement * 0.25 + upward offset
P2 = P3 - horizontal displacement * 0.25 + upward offset
position(t) = cubic_bezier(P0, P1, P2, P3, ease_in_out(t))
```

- Use a stable cubic Bézier helper with unit tests for endpoints.
- Clamp control points to a safe display region; do not let the entire bird vanish beyond screen edges.
- Use a moderate speed, approximately **120–280 px/sec**, adjusted by path length and screen scale. A short trip should not last 8 sec, and a long trip should not jump across the screen.
- Flap wings at roughly **6–10 cycles/sec** in flight, with frame-rate-independent phase accumulation.
- Rotate/flip horizontally based on movement direction. Limit body tilt to approximately ±15°.
- Put branch geometry relative to the **foot anchor**, not window center. When perched, the bottom of the feet should meet the branch top within a few pixels.
- A branch should not travel visibly with the bird in flight. Fade it out during takeoff and fade in near the landing coordinate.
- Prefer random perches away from the common left-edge desktop icon column, but do not try to enumerate or move the user's icons.

For MVP, constrain flight to the **primary monitor's usable region**. The app must handle secondary displays by simply avoiding them, without input or display artifacts.

## 9. Mouse Interaction Specification

### Passive polling

- Poll cursor position at **15–30 Hz**, independent of animation FPS.
- Keep only current/previous samples in RAM; never save cursor trajectories.
- First gate on confirmed desktop exposure; then transform global pointer coordinates to pet-local coordinates.
- Use a simplified elliptical/polygonal bird hit shape, not the full transparent surface or branch bounds.

### Reactions

| Condition | Reaction | Rate limit |
|---|---|---|
| Cursor within ~160 px of head on desktop | Bird looks/tilts toward pointer. | Continuously eased, no state interruption. |
| Cursor inside bird silhouette for >300 ms | Blink or crest bob. | At most once every 3 sec. |
| Left-button rising edge over bird silhouette, while desktop is the actual hit target | Visual chirp or excited head tilt. | At most once every 2 sec. |
| Cursor moves quickly toward a perched bird | Optional small startle/hop. | At most once every 15 sec. |
| Pointer over browser, app, taskbar, or unknown window | Ignore. | Always. |

The cursor must remain visually and behaviorally unchanged. No cursor grabbing, custom pointer replacing, input blocking, or synthetic mouse messages. The bird does **not** need to be draggable in MVP.

## 10. Rendering and Performance

- Render using antialiased vector shapes or original bundled SVG assets if necessary; do not download unlicensed assets at runtime.
- Small alpha-transparent surface, with explicit clear-to-transparent between frames.
- Draw order: branch -> tail -> back wing -> body -> head/crest/face -> front wing -> feet/details (adjust so feet grip branch convincingly).
- Use `QTimer` or Qt animation scheduling with time-based motion: target **30 FPS while moving**, **10–15 FPS while idle**, and only necessary updates when paused.
- Use cached brushes/paths and avoid creating large images every frame.
- No busy loops, global hooks, or repeated shell enumeration on every animation frame.
- Suggested performance targets on a typical modern machine: average CPU comfortably below **3%**, memory ideally below **150 MB**. These are targets, not hard prerequisites for correctness.
- Avoid sounds by default. Never play audio when an ordinary application has focus unless the user opts in.

## 11. Tray, Configuration, and Lifecycle

### Tray menu

```text
Cockatiel Desktop Pet
--------------------
Resume / Pause
Fly Now
Mouse Interaction: On / Off
--------------------
Quit
```

- Use `QSystemTrayIcon`; the app should not keep a normal main window visible.
- Pausing should stop autonomous flight and expensive rendering, without losing tray control.
- Quit must stop timers, destroy native child windows, release handles, and exit cleanly.
- Multiple launches must not create multiple pets. Use a single-instance lock (e.g. named mutex or `QLocalServer`).
- Prefer no autostart for MVP; optional future opt-in only.

### Config file

Store a validated JSON document under `%APPDATA%\CockatielDesktopPet\config.json`:

```json
{
  "schema_version": 1,
  "pet_scale": 1.0,
  "mouse_interaction_enabled": true,
  "paused": false,
  "idle_min_seconds": 20,
  "idle_max_seconds": 55,
  "active_fps": 30,
  "idle_fps": 12,
  "audio_enabled": false,
  "show_on_primary_monitor_only": true
}
```

Handle missing, malformed, or outdated config by loading safe defaults; do not crash at startup. Use atomic writes if practical.

## 12. Error Handling and Special Cases

- **Explorer restart:** hide, detect recreated wallpaper host, reattach safely; avoid ghost windows.
- **Windows display scaling (100%, 125%, 150%, mixed DPI):** correctly map physical mouse coordinates to Qt coordinates.
- **Resolution or primary-monitor change:** recompute screen bounds, reattach/reposition if needed.
- **Sleep/hibernate/resume:** cap large elapsed time; never advance flight by minutes in one frame.
- **Fullscreen games and apps:** bird is naturally behind them; optionally suspend most animation to save resources.
- **Desktop icon clicks and right-click menu:** original click/context menu works and the pet does not activate.
- **Windows taskbar and Start menu:** do not draw over or react to taskbar/Start; no taskbar obstruction.
- **Host not found or incompatible desktop composition:** stay hidden, tray notification + diagnostic log; never open a full-screen overlay as a fallback.
- **Permission/UIPI restrictions:** no administrator privilege should be necessary; degrade gracefully.
- **Unsupported platforms:** exit with a clear unsupported-platform message (not a Python stack trace).

## 13. Implementation Order for Codex

Implement in the following sequence, producing working commits/changes at each step.

### Milestone A — Desktop host proof of concept (P0; do first)

- Create minimal PySide6 + Win32 app with tray and a small, opaque test marker.
- Discover and bind to an appropriate desktop `WorkerW`/wallpaper host.
- Replace marker with a small alpha-transparent, pass-through drawing surface.
- Confirm visually on Windows that normal apps hide the surface, desktop icons remain clickable, and the surface never activates.
- Implement fail-closed behavior. **Do not continue using an unsafe overlay if this milestone fails.**

### Milestone B — Cockatiel and branch (P0)

- Implement an original vector cockatiel with head/crest/orange cheek/wings/tail/feet.
- Add idle pose, blink, subtle breathing, and branch attached to feet while perched.
- Add proper transparent repaint and scaling.

### Milestone C — Autonomous flight (P1)

- Implement state machine and seeded, bounded flight planner.
- Add takeoff, flapping, smooth path, landing and branch transitions.
- Ensure no teleports, no off-screen perches, and long randomized idle periods.

### Milestone D — Mouse interaction (P1)

- Implement desktop-only pointer classification.
- Add head tracking, hover reaction, and passive click reaction.
- Check mouse pass-through while using desktop icons and ordinary applications.

### Milestone E — Polish, recovery, packaging (P1)

- Tray actions, config load/save, single instance, Explorer restart handling.
- Build script, README, automated tests, performance checks, and manual QA notes.

## 14. Automated Tests

Use `pytest` and mocks/fakes to test behavior without requiring Explorer or Win32 on the CI/test machine.

- `test_state_machine`: valid transitions; long idle period; reaction cooldown; Pause behavior; deterministic random seed.
- `test_flight`: Bézier starts/ends exactly; smooth progress; no teleport; bounded destination; elapsed-time independence.
- `test_geometry`: bird/branch fit within primary monitor including negative coordinate virtual desktops; DPI coordinate conversion; foot/branch alignment.
- `test_interactions`: hover/click only for desktop-exposed pointer; app/taskbar clicks ignored; rising-edge click only; cooldown honored; mouse interaction toggle respected.
- `test_config`: defaults, invalid JSON, bounds validation, persistence.
- `test_desktop_host` (mocked): no host -> no visible window; dead host -> hide; reattachment -> visible only after success; style flags never become topmost.

Tests should not need to modify Explorer or send synthetic input to other applications.

## 15. Windows Manual Acceptance Checklist

Codex should add this exact checklist to README or a dedicated QA section and mark unexecuted items as **not yet verified** if working outside Windows.

- [ ] The bird is visibly a cockatiel and has a transparent background.
- [ ] It starts perched on a short branch with feet aligned to the branch.
- [ ] It flies between at least two perches using a continuous animated trajectory.
- [ ] The branch is absent during mid-flight and reappears for landing/resting.
- [ ] Hovering near the bird on the desktop produces a subtle reaction.
- [ ] Clicking through the bird does not prevent selecting or opening a desktop icon.
- [ ] Drag-selecting desktop icons and right-clicking the desktop still work normally.
- [ ] Open Notepad/browser and position it over the bird: bird is entirely **behind** the application window, never drawn on top.
- [ ] Typing, scrolling, and dragging in other apps remain unaffected.
- [ ] Bird is absent from Alt+Tab and does not steal focus or show a regular taskbar button.
- [ ] Fullscreen apps, Start menu, and taskbar are unobstructed.
- [ ] Pause/Resume, Fly Now, and Quit work from the tray.
- [ ] Explorer restart causes graceful hide/re-attachment, without duplicate birds.
- [ ] Reboot/relaunch and screen resolution/DPI changes do not corrupt placement.
- [ ] Windows 10/11 compatibility claims are limited to versions actually tested.
- [ ] If desktop attachment fails, the visual pet stays hidden: **no unsafe floating-window fallback**.

## 16. Definition of Done

The MVP is complete only when:

1. The source code is runnable on Windows with documented commands.
2. The cockatiel animates, flies independently, lands on a branch, and responds subtly to the cursor.
3. Desktop-only layering and click-through are demonstrated on a real Windows system; if real validation is unavailable, clearly document the unverified native integration and provide reproducible manual test steps instead of claiming success.
4. The app remains non-intrusive with normal software, desktop icons, and taskbar usage.
5. Tests are present and passing in the environment where they can execute.
6. Tray controls, fail-closed error handling, and graceful Quit are implemented.
7. The project includes `README.md`, `pyproject.toml`, a Windows packaging script, and a known-limitations section.

## 17. Required Commands and Deliverables

Create a standard editable Python package. Document equivalent commands for PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m cockatiel_pet
python -m pytest -q
.\scripts\build_windows.ps1
```

Deliver:

- Full implementation under `src/cockatiel_pet/`.
- Unit tests under `tests/`.
- An executable build script and documented location for `dist/CockatielDesktopPet/`.
- `README.md` with installation, controls, architecture, OS assumptions, known limitations, and manual test instructions.
- No external copyrighted art and no unexpected network access.

## 18. Direct Instructions to Codex

**Implement this specification as working software, not as another specification.** Inspect the current repository first. If empty, create the project structure. Prioritize the desktop integration proof of concept over visual polish. Use clean interfaces and testable pure-Python state/geometry modules. Do not weaken the desktop-only or pass-through requirements to make a quick demo look functional. If a Windows-native behavior cannot be tested in your environment, implement it conservatively, include logs and a reproducible manual validation procedure, and explicitly state that it remains unverified. Run available tests before reporting completion, and list any remaining blockers precisely.

## 19. Technical References

The following are API references, **not guarantees that an undocumented WorkerW approach works identically on every Windows build**.

- [Microsoft: `SetParent` and required child/popup style adjustments](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setparent)
- [Microsoft: window relationships, layered child windows, alpha hit-testing, and transparency](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features)
- [Microsoft: `SendMessageTimeoutW`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw)
- [Microsoft: `WindowFromPoint`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-windowfrompoint)
- [Microsoft: `GetAsyncKeyState`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate)
- [Qt for Python: `QWindow` and embedding limitations](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QWindow.html)
- [Community discussion of Windows 11 wallpaper/WorkerW compatibility difficulties](https://stackoverflow.com/questions/78880999/draw-on-the-windows-11-wallpaper-in-c-qt)
