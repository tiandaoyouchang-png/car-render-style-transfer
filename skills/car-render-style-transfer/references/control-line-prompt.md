# Control-Line Prompt

Prompt version: `control-line-cad-v1`.

Use this when creating `CONTROL_LINE_IMAGE` from `SOURCE_IMAGE`. The control line is the structural anchor for all later rendering. Do not shorten this prompt for production work.

```text
Convert SOURCE_IMAGE [file/asset name and short visual identity] into an engineering-drawing style automotive structural control image.

Use only SOURCE_IMAGE. Do not use STYLE_REFERENCE_IMAGE. Do not use previous generated candidates. Do not borrow vehicle shape, fascia, lamps, wheels, proportions, crop, or scale from any other image in the conversation.

This is not hand-drawn line art, not an illustration, not a sketch, not a concept design drawing.
Draw it as an automotive engineering drawing / CAD technical drafting / industrial design structural blueprint.

Core goal:
strictly preserve the original vehicle structure and convert the source image into a clean, precise, readable engineering drawing for structure control.

Strictly preserve:
- original vehicle silhouette
- original body proportions
- original wheel positions
- original wheelbase
- original stance
- original tire size
- original wheel arch relation
- original wheel design and spoke layout
- original front or rear fascia
- original lamp shapes and internal lamp boundaries
- original grille, intakes, vents, sensors, and plate block
- original windshield, side glass, and rear quarter glass
- original A/B/C pillar positions
- original mirrors
- original roof details and roof modules
- original body openings
- original door seams, character lines, trim boundaries, wheel arches, and panel gaps
- original camera angle, perspective, crop
- original vehicle position and scale in frame

Composition requirements:
- fixed 16:9 aspect ratio unless the source task explicitly requires another ratio
- preserve the source vehicle's original position, scale, and empty-space distribution unless the user explicitly requests normalized framing
- do not normalize vehicle size
- do not enlarge a small source vehicle into a full-frame vehicle unless requested
- if the source vehicle is small in frame or has large empty space, preserve that scale and empty-space distribution
- keep the original 3D perspective and composition logic
- make it suitable as a structural control drawing

Linework requirements:
- pure white background
- crisp black vector-like lines
- smooth, stable, continuous, precise linework
- no hand-drawn wobble
- no sketchy strokes
- slightly heavier outer silhouette lines
- medium-weight major structural lines
- thinner internal detail lines
- clear line hierarchy like CAD / technical drafting output
- the overall result should look like an automotive engineering drawing, not a line-art illustration

Do not:
- redesign the vehicle
- beautify or stylize the form
- simplify or reinterpret the structure
- make it artistic
- make it illustrative
- make it sketch-like
- add shading
- add gray tones
- add color
- add materials
- add highlights
- add reflections
- add background elements
- add text
- add nonexistent structural lines
- borrow any shape, lamp, wheel, fascia, or proportion from the style reference

The final result should look like an automotive CAD technical drawing / industrial design engineering blueprint, not an artistic car line drawing.
```

## Acceptance Check

Reject and regenerate the control line if any of these fail:

- source silhouette, wheel centers, wheelbase, stance, crop, or perspective changed
- front/rear fascia, lamp shapes, grille/openings, vents, sensors, or plate block changed
- wheel design or spoke layout was simplified beyond recognition
- windows, A/B/C pillars, mirrors, roof modules, door seams, trim, or panel gaps drifted
- linework looks sketchy, illustrative, shaded, colored, noisy, or over-cleaned
- vehicle scale, position, or empty-space distribution differs from the source
- vehicle was enlarged, normalized, or re-cropped when source scale/crop should be preserved
