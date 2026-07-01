# Paint Luminance Calibration

Use this reference when the user asks for consistent car paint, batch uniformity, or numerical analysis of reference highlight and shadow brightness.

The goal is to match the reference's paint brightness distribution, not simply make every car brighter or whiter.

## Measurement Method

Sample only visible painted body panels from `STYLE_REFERENCE_IMAGE`.

Include:

- hood, fenders, doors, quarter panels, painted pillars, painted bumpers
- local highlight bands, broad midtone panels, and painted shadow bands

Exclude:

- glass, tires, wheels, black cladding, grilles, lamps, logos, plates, brake calipers, background, ground shadow
- colored reflections that are not part of the body paint

Record both:

- `HSB_B` / HSV value, 0-100: useful for prompt targets and brightness consistency
- `L*`, 0-100: perceptual lightness, useful for visual audits

## Dynamic Calibration Workflow

For every new `STYLE_REFERENCE_IMAGE`, measure a fresh paint luminance target. Do not reuse values from another reference image unless the user explicitly asks to keep that reference style.

Recommended percentile buckets after sampling paint-like pixels:

| Paint zone | Suggested percentile source | Usage |
|---|---|---|
| dark painted shadows | lower paint distribution, around p5-p25 | lower doors, bumper recesses, lower fender curvature |
| controlled midtones | middle paint distribution, around p35-p65 | main body panels, broad door surfaces |
| main highlights | upper paint distribution, around p75-p95 | hood crown, shoulder line, fender crowns, upper door bands |
| brightest accent highlights | top paint distribution, around p95-p99 | narrow specular ridges only, not broad body panels |

Record the measured numbers in the worksheet and job record before writing the final render prompt.

Dynamic prompt wording:

```text
Match this STYLE_REFERENCE_IMAGE's measured paint luminance distribution: dark painted shadows HSB_B [shadow_B_min]-[shadow_B_max], controlled midtones HSB_B [midtone_B_min]-[midtone_B_max], main highlights HSB_B [highlight_B_min]-[highlight_B_max], and only narrow brightest accent highlights HSB_B [accent_B_min]-[accent_B_max]. Keep L* roughly [shadow_L_min]-[shadow_L_max] in painted shadows, [midtone_L_min]-[midtone_L_max] in midtones, [highlight_L_min]-[highlight_L_max] in main highlights, and [accent_L_min]-[accent_L_max] only on small specular accents. Do not make the whole vehicle bright white, do not flatten contrast, and do not let broad panels exceed the measured reference highlight range.
```

## Consistency Rules

- Use the same measured calibration ranges for every car in a batch only when they share the same style reference.
- Re-measure when the style reference changes, even if the paint still looks silver.
- Keep broad body panels in the midtone range; reserve the brightest range for narrow highlight bands.
- If a result looks flat, deepen adjacent shadows before increasing global brightness.
- If a result looks too white, lower midtones first and keep only thin specular bands near the brightest range.
- If the source car has different geometry, move the highlight bands to equivalent body forms rather than copying the reference vehicle's shape.
