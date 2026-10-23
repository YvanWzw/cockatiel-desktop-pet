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
