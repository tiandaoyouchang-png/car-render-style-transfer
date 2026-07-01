# Prompt Template

Use this template to build image-to-image prompts for one isolated car at a time. Keep the prompt compact, factual, and role-separated. Replace bracketed slots and delete unused lines before generation.

Template version: `render-template-v2.1`.

## Prompt Assembly Rules

1. Include only one `SOURCE_IMAGE`, one source-derived `CONTROL_LINE_IMAGE`, and one `STYLE_REFERENCE_IMAGE` per call.
2. Put source-lock facts before style facts.
3. Describe the reference as a lighting/material recipe, not as a vehicle to copy.
4. Use the selected parameter profile wording exactly unless a failure-recovery step requires a targeted change.
5. Do not paste the full worksheet into the prompt. Convert it into short, concrete facts.
6. Do not include unused placeholders or contradictory composition instructions.

## Control-Line Prompt

Use `references/control-line-prompt.md` when creating `CONTROL_LINE_IMAGE` from `SOURCE_IMAGE`. The compact version below is only for quick tests; production jobs should use `control-line-prompt.md`.

```text
Convert SOURCE_IMAGE [file/asset name and short visual identity] into an automotive engineering-drawing style structural control image.

Use only SOURCE_IMAGE. Do not use STYLE_REFERENCE_IMAGE, previous generated candidates, or any other vehicle image when creating this control line.

Purpose: create a precise structure-control drawing for a later image-to-image render. This is not a sketch, illustration, concept drawing, beautified redesign, or artistic line art.

Strictly preserve the source vehicle:
- silhouette, body proportions, stance, wheelbase, wheel centers, tire size, and wheel arch relationship
- visible wheel design and spoke layout
- fascia, lamp shapes, grille/openings, vents, sensors, plate block, bumper geometry
- hood line, roofline, beltline, underbody line, mirrors, pillars, windows, trim, door seams, panel gaps
- original camera angle, perspective, crop, vehicle position, scale in frame, and empty-space distribution

Line style:
- pure white background
- crisp black vector-like linework
- heavier outer silhouette, medium major structure, thinner internal detail lines
- smooth continuous CAD / technical drafting feel

Do not add shading, gray tones, color, materials, reflections, background elements, text, labels, invented lines, simplified geometry, or style-reference features.
Do not normalize vehicle size or enlarge a small source vehicle into a full-frame vehicle unless explicitly requested.
```

## Final Render Prompt

```text
INPUT ROLES
Create one automotive CGI render using three references:
1. SOURCE_IMAGE = only vehicle identity and fine-detail source.
2. CONTROL_LINE_IMAGE = strict geometry, stance, camera, crop, and panel-layout control.
3. STYLE_REFERENCE_IMAGE = lighting, paint behavior, material, reflection quality, and render finish only.

PRIORITY ORDER
1. Preserve SOURCE_IMAGE vehicle identity and CONTROL_LINE_IMAGE geometry.
2. Restore fine source details not captured by linework.
3. Apply STYLE_REFERENCE_IMAGE lighting/material/render style.
4. Apply background and shadow requirements.

SOURCE LOCK FACTS
Preserve these exact source facts:
- vehicle type/proportion: [source vehicle type, roofline, stance]
- silhouette/crop/camera: [hood, roof, rear/side, underbody, perspective, scale]
- fascia/openings: [front or rear fascia, grille/intakes/vents/sensors/plate block]
- lamps/glass: [lamp shapes/DRL/tail lamp, windshield/side glass/rear quarter]
- wheels: [wheel center positions, tire size, wheel arch relation, spoke pattern]
- details: [mirrors, handles, trim, roof modules, panel gaps, badges/plate treatment]

STRUCTURE LOCK
Do not redesign, simplify, beautify, resize, reposition, or borrow parts from STYLE_REFERENCE_IMAGE or any other vehicle. Keep wheelbase, wheel centers, stance, tire size, wheel design, fascia, lamps, grille/openings, hood, roofline, pillars, window layout, mirrors, seams, creases, trim boundaries, panel gaps, perspective, crop, and vehicle scale consistent with SOURCE_IMAGE and CONTROL_LINE_IMAGE.

STYLE RECIPE TO TRANSFER
Use STYLE_REFERENCE_IMAGE only as this render recipe:
- render style: [premium CGI / soft studio / dark studio / catalog / other]
- paint color expression: [hue, saturation, brightness, metallic/pearl/clearcoat behavior]
- highlight behavior: [softbox shape, mid-body band, roof/hood highlights, rim light]
- shadow behavior: [glass darkness, lower-body shading, contrast, cool/warm temperature]
- camera/composition target: [keep source crop/camera OR match selected reference composition fields]

PAINT AND MATERIAL
[paint target and profile wording]
Keep paint controlled and source-geometry-consistent. Preserve source panel boundaries and reflections as neutral automotive studio bands. Avoid unintended hue shifts, especially purple/violet or green-tinted reflections.

COMPOSITION AND CAMERA
[composition mode: keep source composition / match reference scale only / match selected reference camera feel while preserving source geometry]
Output aspect ratio: [aspect ratio].
Vehicle occupancy: [same as source / specific percentage or frame position].

BACKGROUND AND SHADOW
[background requirement]
[shadow requirement]

FORBIDDEN ARTIFACTS
No green spill, green reflections, ground reflections, floor texture, horizon, cyclorama, lit green room, physical green-screen interpretation, horizontal floor streaks, wavy ground lines, watermarks, readable text, new badges, new logos, or plate writing unless explicitly requested. If style conflicts with source structure, choose source structure.

PARAMETERS
- profile: [selected profile]
- render_prompt_version: render-template-v2.1
- control_line_prompt_version: [control-line-cad-v1 unless overridden]
- candidate_count: [4 single / 2 batch / user-specified]
- structure_priority: [profile value]
- style_strength: [profile value]
- lighting_strength: [profile value]
- gloss_strength: [profile value]
- paint_hsb or paint target: [profile value]
- retry_rule: restart from original SOURCE_IMAGE + CONTROL_LINE_IMAGE + STYLE_REFERENCE_IMAGE; never from a generated candidate.
```

## Background Blocks

Use exactly one block.

### Pure Green Cutout

```text
Background: exact pure solid green #00FF00 / RGB(0,255,0), edge to edge, as a flat 2D compositing color plate. It is not a physical floor, green screen room, cyclorama, lit surface, or environment. No gradient, texture, horizon, floor seam, ground plane, or green light spill.
Shadow: only a soft neutral contact shadow under tires and chassis, with blurred feathered edges and natural opacity falloff.
```

### Studio Background From Reference

```text
Background: use only the non-vehicle studio mood from STYLE_REFERENCE_IMAGE. Do not copy any reference vehicle geometry, wheels, fascia, lamps, crop errors, logos, text, or scene-specific clutter. Keep background secondary and structure-safe.
Shadow: soft physically plausible contact shadow consistent with the selected studio lighting recipe.
```

### Transparent/Cutout-Ready Neutral

```text
Background: clean neutral cutout-ready studio plate with no horizon line, no floor texture, no environmental clutter, and no color spill onto the car. Keep the car edge clean for compositing.
Shadow: subtle neutral contact shadow only.
```

## Compact Style Recipe Examples

Use these as wording patterns, not fixed defaults.

### Cool Silver Premium CGI

```text
Cool pearl silver-gray paint, HSB around H=216 and S=10, medium-light midtones about half a stop darker than bright white. Satin-gloss clearcoat, soft silver-blue roof/hood highlights, broad neutral cool-gray studio reflection bands, dark blue-gray lower-body shading, no purple/violet shift and no green tint.
```

### Dark Studio Gloss

```text
Premium dark studio CGI with controlled high-gloss clearcoat, deep neutral shadows, narrow softbox highlights along roof/hood/shoulder, smoked glass, restrained rim light, and crisp panel definition. Keep midtones controlled so detail does not disappear.
```

### Side-Profile High-Contrast Silver

Use for side-view or near-side-profile vehicles that look flat or under-highlighted.

```text
Side-profile high-contrast cool silver CGI paint: keep overall midtones controlled and slightly darker than bright white, while adding brighter clean silver-blue specular bands along the hood crown, upper shoulder line, beltline, window lower edge, side-door curvature, fender crowns, wheel arch lips, and rocker-to-door transition. Deepen adjacent cool blue-gray shadows on the lower doors, side skirts, wheel arches, and underbody so the high points read brighter. Do not globally raise exposure, do not wash out lamps, panel gaps, wheel spokes, orange brake calipers, or source design details.
```

### Catalog Soft Studio

```text
Clean catalog-style automotive CGI with soft overhead light, broad low-contrast body highlights, neutral reflections, readable lamp/grille/wheel detail, and natural soft contact shadow. Keep material polished but not over-glossy.
```
