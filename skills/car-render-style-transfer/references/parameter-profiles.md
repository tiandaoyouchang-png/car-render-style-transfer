# Parameter Profiles

Choose one profile before building the final render prompt. Use the wording consistently across retries so outputs remain comparable. Change only one parameter group at a time during recovery.

## fidelity-lock

Use when the source vehicle must remain almost exact, when the first candidate borrows reference-vehicle geometry, or when the source is structurally complex.

- `structure_priority`: maximum
- `style_strength`: low to medium-low
- `lighting_strength`: medium
- `gloss_strength`: medium
- `composition`: keep source crop, source camera, source scale, source perspective
- `candidate_count`: 4 single / 2 batch
- Prompt emphasis: repeat source-lock facts, keep style recipe short, forbid borrowing reference fascia/wheels/lamps/proportions.

Recommended paint wording:

```text
Apply the reference lighting and material finish subtly while preserving source geometry and source design details exactly. Do not let the style reference change body shape, wheel design, fascia, lamps, crop, or perspective.
```

## balanced-style

Use as the default single-car profile when both structure and reference style matter.

- `structure_priority`: very high
- `style_strength`: medium-low to medium
- `lighting_strength`: medium
- `gloss_strength`: medium
- `composition`: keep source geometry; optionally match reference vehicle scale or negative space if explicitly selected
- `candidate_count`: 4
- Prompt emphasis: source facts first, style recipe second, no reference-vehicle design transfer.

Recommended paint wording:

```text
Transfer the reference's lighting recipe, paint behavior, reflection quality, and CGI polish while keeping the source vehicle identity and control-line geometry unchanged.
```

## style-forward

Use only when the user explicitly prioritizes matching the visual mood of the style reference and accepts a slightly stronger style influence. Do not use if previous outputs changed vehicle identity.

- `structure_priority`: very high
- `style_strength`: medium to high
- `lighting_strength`: high
- `gloss_strength`: medium to high
- `composition`: may match selected reference camera feel, vehicle occupancy, or lighting contrast; never copy reference body design
- `candidate_count`: 4
- Prompt emphasis: separate style recipe from vehicle geometry; keep source-lock facts mandatory.

Recommended paint wording:

```text
Strongly match the reference's lighting contrast, paint finish, softbox highlight shape, glass darkness, and premium CGI rendering quality, while preserving the source vehicle structure exactly.
```

## side-profile-highlight

Use when a side-view or near-side-profile car output keeps structure but looks flat, low-contrast, or lacks bright body highlights. This is an overlay profile: combine it with `balanced-style`, `fidelity-lock`, `strict-green-cutout`, or `batch-silver-green` rather than replacing the base profile.

- `structure_priority`: keep the base profile value
- `style_strength`: keep the base profile value
- `lighting_strength`: medium to high
- `gloss_strength`: medium to high
- `composition`: keep source/control crop, camera, wheelbase, side profile, and vehicle scale
- Prompt emphasis: raise specular highlight contrast locally, not global exposure.

Required side-view contrast wording:

```text
Increase side-profile paint contrast without making the whole car brighter. Keep midtones controlled and slightly darker than bright white, but add brighter clean silver-blue specular highlight bands along the hood crown, upper shoulder line, beltline, window lower edge, door curvature, front/rear fender crowns, wheel arch lips, and rocker-to-door transition. Deepen adjacent cool blue-gray shadows under the beltline, lower doors, side skirts, wheel arches, and underbody so the highlights read brighter. Do not wash out panel gaps, lamps, wheel spokes, or source design details.
```

## strict-green-cutout

Use when the final image must be composited cleanly or the user requests a pure green background.

- `structure_priority`: very high
- `style_strength`: medium-low
- `lighting_strength`: medium
- `gloss_strength`: medium, but avoid green reflections
- `background`: exact solid `#00FF00` / `RGB(0,255,0)` edge-to-edge
- `shadow`: soft neutral contact shadow only
- `candidate_count`: 4 single / 2 batch
- Prompt emphasis: flat 2D color plate, not a physical room or floor.

Required background wording:

```text
Background: exact pure solid green #00FF00 / RGB(0,255,0), edge to edge, as a flat 2D compositing color plate. It is not a physical floor, green screen room, cyclorama, lit surface, environment, or source of green illumination. No gradient, texture, horizon, floor seam, ground plane, or green light spill.
```

## batch-silver-green

Use for repeated car batches that need unified silver paint and pure green background.

- `structure_priority`: maximum
- `style_strength`: low to medium-low
- `lighting_strength`: medium
- `gloss_strength`: medium
- `paint_hsb`: H=216, S=10, medium-light brightness about half a stop darker than bright white
- `background`: exact solid `#00FF00`
- `candidate_count`: 2 per source car
- `composition`: keep each source car's crop and camera unless the batch spec requires normalized scale
- Prompt emphasis: consistent paint, no purple shift, no green spill, no floor interpretation.

Required paint wording:

```text
Use unified cool pearl silver-gray paint, HSB around H=216 and S=10, with medium-light midtones about half a stop darker than bright white. Keep satin-gloss clearcoat, soft silver-blue highlights, neutral cool gray/black studio reflection bands, and cool blue-gray lower-body shadows. Do not shift purple/violet, warm white, bright white, or green-tinted.
```

## reference-studio

Use when the background and studio atmosphere should follow the reference, but the vehicle must remain the source.

- `structure_priority`: very high
- `style_strength`: medium
- `lighting_strength`: medium to high
- `gloss_strength`: medium
- `background`: reference studio mood only, no reference vehicle geometry or scene clutter
- `candidate_count`: 4
- Prompt emphasis: copy light and mood, not vehicle design.
