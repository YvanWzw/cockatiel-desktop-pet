# Feathered cockatiel artwork — 2026-10-26

This is original artwork generated with Codex's built-in **imagegen** tool.
The running application does not generate images and has no network dependency.
No images, video, models, or files were extracted from NetEase Cloud Music.
Its already-open pet UI was visually observed only to understand the requested
level of realism: cream feathers, slender yellow crest, natural anatomy, and
quiet companion gestures. No screenshots of the user's music account are saved
in this repository.

`cockatiel-atlas.png` is the selected generated PNG, preserved unchanged.
`atlas.json` describes source regions and anatomical anchors. Six standing poses
are normalized to the same foot position. A detailed wing region drives a
continuous two-wing rig with a stable torso/head, rather than jumping between
different generated flight bodies. All compositing uses premultiplied alpha.

## Generation prompt

Use case: stylized-concept. Asset type: production transparent PNG sprite atlas
for an original Windows cockatiel companion, a complete 3 by 3 grid of nine equal
square cells. Create one original consistent lifelike lutino cockatiel,
cream-white feathered body, softly lemon-yellow face, fine slender swept yellow
crest, vivid but natural orange cheek patches, small glossy black eyes with
realistic tiny catchlights, pale horn curved beak, pale pink zygodactyl feet,
long tapered layered ivory tail. Premium near-photoreal 3D pet rendering with
fine down and overlapping wing feathers, gentle studio light. Natural juvenile
cockatiel anatomy, moderately round affectionate body, head not a giant cartoon
ball, no outlines, no flat vector geometry, no plastic toy look, not a copy of
any brand character. Orthographic three-quarter view facing screen right.
Transparent canvas and spaces between birds; no ground, shadows, branch, text,
grid lines, border, labels or watermark. Fixed camera, identical scale and
identity, same body center and foot/contact anchor; never crop crest, tail or
wing tips. Standing poses: neutral, blink, curious tilt, look toward viewer,
preen, partial wing stretch. Flying poses: wings up, level, down, with stable
torso and head. Fine feather detail readable around 150 logical pixels tall.
Use actual alpha transparency, never a painted checkerboard.

## Final refinement prompt

Edit target: the supplied 3x3 cockatiel sprite atlas. Keep the same bird identity,
lifelike white and cream feathers, yellow crest, orange cheeks, camera
orientation and nine pose meanings. Remove all stray white/yellow/red pixels,
speckles, grain, shadows, halos and colored remnants outside each bird. The
entire space between birds must be clean true transparent alpha=0; only birds
are nontransparent. Natural feather cutout edges. Re-layout the birds into
equal 3x3 cells with generous transparent gutters. Scale all nine birds
consistently smaller, about 70 percent of their previous size. Each bird,
including every wing tip and tail, should fit wholly inside its cell with
transparent margins. No drawn cell borders, text or checkerboards. Standing
feet use the same normalized baseline and contact anchor. Flight torso/head
positions should match across the three flight frames. Leave empty areas fully
transparent. This is an animation asset, not a presentation board.

The actual generated layout is 1254 × 1254; the source metadata accounts for
the measured layout rather than assuming the requested output resolution.
