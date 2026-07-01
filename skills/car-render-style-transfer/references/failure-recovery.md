# Failure Recovery

Use this only after auditing candidates with the worksheet. Do not recover by editing a generated candidate. Restart every retry from the original `SOURCE_IMAGE`, accepted `CONTROL_LINE_IMAGE`, and `STYLE_REFERENCE_IMAGE`.

Before each retry, update the job record with `retry_number`, `failure_category`, `failed_quality_gates`, `changed_parameter_group`, and `next_action`. Change exactly one parameter group per retry unless the control line itself failed.

## Retry Ladder

- **R0 baseline**: selected profile, normal prompt.
- **R1 targeted correction**: keep the same profile and change exactly one failed parameter group.
- **R2 profile correction**: switch to a stricter profile, usually `fidelity-lock` or `strict-green-cutout`.
- **R3 control correction**: regenerate or replace `CONTROL_LINE_IMAGE`; consider hybrid control if geometry still drifts.

Do not change structure language, paint target, lighting, background, and composition all at once. That makes the result non-diagnostic.

## Failure Table

| Failure | Likely cause | Next action |
|---|---|---|
| Vehicle becomes another model | style reference is influencing geometry | restart from original inputs; switch to `fidelity-lock`; reduce `style_strength`; add 5-8 specific source-lock facts |
| Front fascia or lamps change | prompt under-specified fine details or control line too simplified | strengthen fascia/lamp facts; use source image for fine details; regenerate control line if needed |
| Wheels move, resize, or change design | control line failed or style borrowed stance | audit wheel centers and wheel arch relation; repeat exact wheel facts; reduce style strength |
| Crop/camera drifts | contradictory composition instructions | choose one composition mode only; remove reference-camera language if source crop should win |
| Reference car shape leaks in | style reference not role-limited | explicitly state style reference controls lighting/material only; forbid borrowing body shape, wheels, fascia, lamps, crop |
| Paint too bright or washed out | highlights raised midtones | keep highlight intensity but lower midtones/shadows by half a stop |
| Contrast too low or highlights too dim | prompt raised style softly but did not specify local specular bands | add `side-profile-highlight` overlay; increase local silver-blue specular bands; deepen adjacent cool blue-gray shadows; do not raise global exposure |
| Silver turns purple | hue drift near HSB 240 | target HSB H=216, S=10; explicitly avoid purple/violet hue |
| Paint becomes green-tinted | green background interpreted as lighting/environment | repeat flat 2D color-plate rule; forbid green reflections/spill on body, glass, wheels, tires, trim |
| Background becomes green room/floor or green gradient | model treats green as physical scene or lighting plate | use `strict-green-cutout`; require one uniform flat raster #00FF00 background pixel value; say no floor, horizon, cyclorama, lit surface, gradient, vignette, or ground plane |
| Ground reflection streaks appear | floor/environment reflections leaking into paint | forbid floor texture, horizontal ground streaks, wavy reflected ground lines; use neutral studio bands only |
| Details disappear | line control used without source-detail restoration | add detail rule: restore lamp internals, grille texture, wheel spokes, trim, sensors from SOURCE_IMAGE |
| Output becomes blurry | iterative editing or overconstrained correction | restart from original inputs; do not use generated candidate; keep prompt shorter and profile-based |
| Windshield or glass has black-white stripes, checkerboard blocks, or noisy patches | transparency checkerboard/source noise/control-line texture leaked into glass rendering | restore smooth continuous dark smoked automotive glass; forbid checkerboard, zebra stripes, patchy blocks, pixel noise, white bars, and texture transfer inside glass |
| A-pillar or windshield edge looks dirty, muddy, smudged, or contaminated | noisy source artifacts or reflection texture collected at the glass/body boundary | clean the A-pillar-to-windshield seam; use crisp black rubber trim and smooth dark glass; forbid dirty gray smears, dust, speckles, blotches, cloudy patches, and muddy edge reflections |
| Glass still looks dirty after cleanup | source glass interior pixels are being preserved as detail | use glass-material override; source controls glass outline/pillars/trim only, not glass interior texture; regenerate glass material from style reference |
| Batch outputs inconsistent | context contamination or profile drift | isolate one car per call; reuse same profile; store source-lock facts per car; avoid carrying previous failures into next car |

## Targeted Correction Blocks

Use one block per retry.

### Structure Correction

```text
Correction for this retry: structure drift was detected. Increase structure priority to maximum and reduce style strength. Preserve SOURCE_IMAGE and CONTROL_LINE_IMAGE geometry exactly, especially [failed parts]. STYLE_REFERENCE_IMAGE must not affect body shape, fascia, lamps, wheels, crop, or perspective.
```

### Paint Correction

```text
Correction for this retry: paint mismatch was detected. Keep the same source geometry and lighting setup, but adjust only paint color/material toward [target]. Do not change wheel placement, fascia, lamp shapes, crop, camera, or background.
```

### Contrast / Highlight Correction

```text
Correction for this retry: the side-view render looked too flat and the body highlights were not bright enough. Keep the same source geometry, crop, camera, paint hue, and background. Change only the lighting/gloss contrast: add brighter clean silver-blue specular highlight bands along [hood crown / upper shoulder line / beltline / window lower edge / side-door curvature / fender crowns / wheel arch lips / rocker-to-door transition], and deepen adjacent cool blue-gray shadows on [lower doors / side skirts / wheel arches / underbody]. Do not globally raise exposure, do not turn the car bright white, and do not wash out source details.
```

### Green Background Correction

```text
Correction for this retry: background or green spill failed. Treat #00FF00 as a flat 2D compositing plate only, not a floor, room, cyclorama, environment, or light source. Remove all green reflections and green tint from body, glass, wheels, tires, trim, and lower panels.
The background outside the car and shadow must be one uniform flat raster color: #00FF00 / RGB(0,255,0). Do not shade, light, vignette, blur, texture, gradient, or perspective-transform the green background. The green area is not a surface and must not receive shadows or reflections.
```

### Composition Correction

```text
Correction for this retry: composition drift was detected. Keep [source/reference-selected] crop, vehicle scale, perspective, and camera feel. Do not change vehicle design, wheel placement, stance, fascia, lamps, or paint target.
If the source vehicle is small in frame or surrounded by large empty space, preserve that source scale and empty-space distribution unless the user explicitly requests normalized framing.
```

### Detail Sharpness Correction

```text
Correction for this retry: fine details became soft. Restore grille texture, lamp internals, wheel spokes, trim boundaries, sensors, panel gaps, handles, roof rails, tire edges, brake calipers, and glass edges from SOURCE_IMAGE while keeping the same style recipe and geometry control. Use crisp high-resolution CGI edges and readable automotive details, not painterly blur, low-resolution smoothing, or softened linework.
```

### Glass Artifact Correction

```text
Correction for this retry: windshield/glass artifacts were detected. Keep the same source geometry, crop, paint, and lighting style, but render the windshield, side glass, and rear quarter glass as smooth continuous dark smoked automotive glass with subtle clean studio reflections. Do not transfer checkerboard transparency patterns, CAD line texture, source noise, black-white stripes, zebra bands, patchy rectangular blocks, white bars, pixel noise, or speckled artifacts into any glass area.
```

### A-Pillar / Windshield Edge Cleanup

```text
Correction for this retry: the A-pillar and windshield edge looked dirty or contaminated. Keep the same source geometry, crop, paint, and lighting style, but clean only the A-pillar-to-windshield boundary. Render the A-pillar as clean painted body/black trim, the windshield edge as crisp black rubber sealing, and the windshield as smooth continuous dark smoked glass. Do not place dirty gray smears, dust, speckles, muddy blotches, cloudy patches, source noise, checkerboard remnants, or busy reflected texture around the A-pillar, windshield edge, mirror base, or front side-window corner.
```

### Glass Material Override

```text
Correction for this retry: source glass texture is contaminating the result. Treat SOURCE_IMAGE glass as a shape and boundary reference only. Preserve the exact windshield outline, side-window outline, A/B/C pillar positions, black trim, mirror base, and glass edge geometry, but do not preserve the source glass interior pixels, texture, transparency artifacts, noise, dirt, cloudy reflections, checkerboard remnants, or speckles. Regenerate all glass interiors from the STYLE_REFERENCE_IMAGE material recipe as clean continuous dark smoked automotive glass with subtle smooth studio reflections.
```

## Acceptance Rule

Accept a candidate only when all Level-1 structure gates pass and all user-critical gates pass. If only non-critical style gates fail, prefer the structurally correct candidate and run a targeted style retry rather than selecting a visually attractive but structurally wrong candidate.
