# Subsequent user requirement — 2026-10-23

The user explicitly requested a change after the original desktop-only
specification: right-clicking the tray icon must allow showing the pet in front
of all applications or hiding it; the application must not be restricted to the
desktop.

This later instruction supersedes the original blanket prohibition on a topmost
pet and the desktop-only display requirement. The application now has three
explicit, persistent choices:

- `desktop`: verified wallpaper child, behind icons and normal application windows.
- `front`: small native topmost popup above ordinary applications, still layered,
  transparent to mouse input, nonactivating and absent from normal taskbar/Alt+Tab.
- `hidden`: no drawing window or animation/pointer timer, tray remains accessible.

Default remains `desktop` for existing installations. Front mode is only created
after an explicit tray/config choice, never automatically on desktop-host failure.
Each switch destroys the old surface before creating another. Pointer reactions
may occur over ordinary applications in front mode, but clicks are never consumed.
The original specification is retained unchanged as the historical input.

## Visual quality update — 2026-10-26

The user asked for a lifelike cockatiel companion resembling the quality of
the NetEase Cloud Music pet currently running on their computer, and authorized
observing its UI. The music pet page and cockatiel preview were visually observed.
No proprietary images, models, account screenshots, or application files were
extracted or copied into this project.

This update supersedes the original requirement to draw the entire bird only
with procedural vector shapes. Version 1.1 bundles original generated feathered
artwork with a local QPainter sprite compositor, a stable neck pivot, detailed
wing layers, short blinks, preening and stretch gestures. It is a 2D layered
animation renderer, not a real-time 3D engine. Desktop/front/hidden behavior,
passive mouse observation, configuration and packaging remain available.

## Four visual corrections — version 1.2.0

The user requested a more screen-facing face, correct claw/branch contact,
coherent flying anatomy and a livelier idle. The user clarified that the actual
desktop pet, rather than the music application's preview, is the reference.
The current computer-use window inventory exposes only the music main window;
the independent desktop pet could not be captured. This limitation was reported
to the user. No claim of observing its desktop animation is made.

Version 1.2 uses new original near-frontal perched artwork with integrated
gripping feet/branch, fixed contact pixels during deformation, continuous
breathing/sway/neck/crest/tail rhythms, and six complete registered airborne cels.
The previous pasted-wing standing-body renderer is removed. The atlas PNGs are
shipped unchanged; crop/registration metadata and the runtime compositor produce
the actual poses shown in the generated previews. The renderer remains 2D.
