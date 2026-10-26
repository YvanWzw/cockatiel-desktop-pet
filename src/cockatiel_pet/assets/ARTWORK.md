# Original cockatiel artwork — version 1.2.0, 2026-10-26

Both PNGs were generated with Codex's **built-in imagegen tool**, transparent
background enabled, and copied unchanged into this directory. No CLI/API fallback
was used. The installed app is fully offline and never generates images.

- `perched-v2.png`: 1254 × 1254 RGBA. Runtime uses neutral and registered blink
  eyes. The generated tilt/preen reference cells are not used for animation.
- `flight-v2.png`: 1536 × 1024 RGBA. Six complete anatomical flight poses.
  The perched sheet was supplied as an identity reference to this generation.
- `atlas.json`: measured source rectangles, scale, and registration anchors.

The perched feet and branch are part of one original render. Runtime deformation
keeps logical rows 164–188 fixed and animates the chest/neck/crest above and tail
below. Blink uses small registered eye patches. Flight selects one complete cel
at a time, including shoulders, torso, tucked feet and tail. It does not attach
a detached wing to a standing body or blend multiple exposed wing positions.

RGB values in fully transparent source pixels are irrelevant to rendering;
Qt converts the source to premultiplied alpha before filtering/compositing.
No external image, 3D model, screenshot, music account data, or proprietary
NetEase asset is included. Only its main-window preview was observable; the
independent desktop pet was **not captured or directly observed**.

## Perched sheet — final prompt

Use case: stylized-concept. Production animation asset sheet for an original lifelike lutino cockatiel Windows desktop companion. A precise 2 columns x 2 rows grid on real transparent background, equal square cells, generous clear gaps. No text or borders. Four full body renders of EXACTLY THE SAME bird on EXACTLY THE SAME narrow horizontal natural brown branch, identical framing, size, anatomy, lighting and contact. Soft realistic 3D feather rendering, cream white body, pale yellow slender swept crest, orange cheek patches, small pale pink beak, glossy dark eyes, detailed soft feathers, pink scaled feet. Camera nearly frontal, body yaw only 15 degrees, both eyes and BOTH orange cheeks clearly visible, bird face looks toward viewer/screen, elegant realistic proportions, long tail visible descending behind to right. Each branch is horizontal and spans 85% cell width near 78% cell height; both feet anatomically wrap over branch with curved toes and dark claws visibly gripping FRONT AND BACK of branch, no flat floor stance or floating feet. Crest top near 12% cell height, feet near78%, tail may descend toward90%. Top left: neutral, eyes open. Top right: identical neutral with eyelids closed for blink (same head position and branch). Bottom left: gentle inquisitive head inclination to viewer left, feet and branch identical to neutral. Bottom right: head tucked to preen shoulder feathers, body and feet and branch identical. Strict isolation, no shadows on background, no white matte or glow. Full natural branch and toes included in every cell. This replaces a too side-on previous bird. Original design, no brand or other app assets.

## Flight sheet — final prompt

Use case: stylized-concept. Input image 1 is IDENTITY / feather-material reference only for the SAME original cream-white lutino cockatiel, not a grid to copy. Create a new production FLIGHT animation sprite sheet, precisely 3 columns x 2 rows equal cells on true transparent background. Six full-bodied, anatomically plausible successive wingbeat phases of the same bird. Each cell isolated with large transparent gutters; NOTHING cut off or shared between cells. No branches anywhere. Near frontal three-quarter camera, face yaw 20 degrees toward viewer right, both eyes readable. Airborne body angled slightly diagonally, long tail streaming down-left, BOTH pink feet tucked neatly under belly, neck extended gently. Same body size, head position, tail, tucked feet, facial proportions, color and scale in all 6 cells; only the complete two wings change. Body center exactly at cell center, head around (55%,42%) of each cell, tail tip around (35%,78%). Wings must attach organically to the shoulders and flow coherently into body plumage, NOT detached wing cutouts. Each wing has feathered upper arm, elbow, wrist and long primary fan. Wingbeat cycle read left to right top then bottom: 1 both wings raised high, 2 wings extended outward/up 35 degrees, 3 both wings wide horizontal, 4 both wings down/out 35 degrees with primary tips lowest, 5 wings loosely flexed down/near body on recovery, 6 wings rising bent at elbows/upwards ready for frame1. Wings fill at most 85% of cell width and 80% height. Maintain exact body identity from reference including creamy white feathering, thin pale yellow crest swept back by air, orange cheek patches, glossy black eyes and pale pink beak. Soft realistic polished 3D feather render with subtle warm studio light. No stylized anatomy, no oversized chest, no extra wings, no duplicate bodies or tails, no detached feathers, no gridlines, labels, background color, floor shadow, outline or glow. All 6 full birds must be the same size and wholly contained.
