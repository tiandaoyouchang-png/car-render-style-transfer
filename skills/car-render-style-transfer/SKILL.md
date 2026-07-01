---
name: car-render-style-transfer
description: Image-to-image workflow for preserving target car geometry while transferring automotive CGI paint, lighting, camera feel, material, and studio render style from a reference image. Use for vehicle image-to-image restyling, car render style transfer, source-derived control lines, unified silver paint batches, green-background cutout renders, batch production, or when outputs drift in body structure, wheel placement, fascia, lamps, crop, perspective, reflections, paint, or background.
---

# Car Render Style Transfer

Use this skill as an inference-time workflow for image-to-image car render style transfer. Do not treat the task as model training, fine-tuning, LoRA, dataset preparation, or weight adaptation. The goal is stable, repeatable generation behavior through controlled inputs, prompt structure, parameter profiles, quality gates, job records, and failure recovery.

Geometry preservation is the success condition. Style quality is secondary.

## Input Roles

Keep the three image roles separate throughout the job.

| Role | Required? | Purpose | May control | Must not control |
|---|---:|---|---|---|
| `SOURCE_IMAGE` | yes | target vehicle identity and fine details | shape, proportions, stance, lamps, grille, wheels, trim, crop, camera | paint target unless explicitly requested |
| `CONTROL_LINE_IMAGE` | yes for production runs | strict structural control from `SOURCE_IMAGE` | silhouette, wheel placement, fascia, window layout, panel boundaries, perspective | color, lighting, material, background |
| `STYLE_REFERENCE_IMAGE` | yes | render style reference | lighting recipe, paint behavior, material, reflection quality, CGI finish | vehicle design, body shape, wheels, fascia, lamps, crop unless explicitly selected |

Do not place multiple source vehicles in one generation context. For batch work, process one source car per isolated call.

## Reproducible Execution Protocol

1. **Reset context for the job.** Start from the original `SOURCE_IMAGE`, the source-derived `CONTROL_LINE_IMAGE`, and the `STYLE_REFERENCE_IMAGE`. Never use a previous generated candidate as the next input.
2. **Create the job record.** Use `references/job-record-template.md` before generation. Record asset paths/IDs, selected profile, prompt versions, and initial decisions. The job record is a production log, not prompt text.
3. **Fill the compact worksheet.** Use `references/analysis-worksheet.md` to extract only the source-lock facts, style recipe, prompt decisions, and audit targets needed for this car.
4. **Calibrate paint luminance from the style reference.** Use `references/paint-calibration.md` when the job needs consistent silver paint, batch consistency, or when outputs look too flat/bright/dark. Record highlight, midtone, and shadow brightness ranges.
5. **Choose one parameter profile.** Use `references/parameter-profiles.md`. Do not improvise parameter language unless a failure requires it.
6. **Create or verify control line.** Use `references/control-line-prompt.md`. Generate the line control from `SOURCE_IMAGE`, not from `STYLE_REFERENCE_IMAGE`. The control-line prompt must name the source file/asset and describe its visible identity so the model cannot confuse it with the style reference. Reject the control line if wheel centers, silhouette, fascia, lamp shapes, window layout, crop, perspective, or source vehicle scale drift.
7. **Update the job record.** Record the accepted control line, control-line prompt version, selected profile, and any rejected control-line attempt.
8. **Build the final render prompt.** Use `references/prompt-template.md`. Fill only the slots that apply. Delete unused placeholders.
9. **Generate candidates.** Use 4 candidates for a single careful render and 2 candidates per car for batch runs unless the user specifies otherwise.
10. **Run quality gates.** Reject candidates that fail any Level-1 structure gate or any requested background/paint gate.
11. **Update the job record after review.** Record candidate IDs, accepted result, rejected candidates, failed gates, failure notes, changed parameter group, and next action.
12. **Recover by changing parameters only.** Use `references/failure-recovery.md`. Restart from original inputs every retry.

## Decision Tree

1. **Is this a batch?**
   - Yes: use one isolated image-to-image call per source car; use `batch-silver-green` or another fixed profile; produce 2 candidates per car.
   - No: use `fidelity-lock` for strict structure or `balanced-style` for normal style transfer; produce 4 candidates.

2. **Is vehicle identity more important than matching the reference style?**
   - Yes or uncertain: use `fidelity-lock`; keep source crop/camera; lower style strength.
   - No, the user asks to match reference mood strongly: use `style-forward`, but keep source geometry as the top priority.

3. **Does the task require pure green background?**
   - Yes: use `strict-green-cutout` or `batch-silver-green`; repeat the flat 2D color-plate rule in the prompt.
   - No: omit green-background constraints unless the source/reference would otherwise create floor or green spill artifacts.

4. **Did the first output drift structurally?**
   - Yes: do not edit the output. Restart from original inputs, switch to `fidelity-lock`, reduce style strength, and strengthen the source-lock facts.
   - No: adjust only the failed style/background/paint parameter group.

## Non-Negotiable Rules

- Use `STYLE_REFERENCE_IMAGE` for lighting, material, color expression, reflection quality, and render polish only.
- When consistent paint is required, match the reference's measured paint luminance ranges, not just the descriptive color name.
- Use `SOURCE_IMAGE` for all vehicle design details that line art cannot express.
- When source glass is noisy, checkerboard-backed, dirty, or low quality, use `SOURCE_IMAGE` only for glass shape, boundary, pillars, and trim. Do not inherit source glass interior pixel texture; regenerate glass material from the style recipe.
- Use `CONTROL_LINE_IMAGE` for geometry, stance, perspective, wheel positions, panel layout, and crop.
- Generate structural controls from the source car that must keep its shape.
- If structure and style conflict, preserve structure and reduce style strength.
- Do not continue from a generated candidate. Every retry starts from the original source, control line, style reference, and explicit parameter changes.
- In batch jobs, do not let previous cars, previous candidates, or previous failure language enter the next car's prompt.

## Control-Line Creation

Default method: create an automotive engineering-drawing / CAD technical drafting style structural control image from `SOURCE_IMAGE` using `references/control-line-prompt.md`. It should be a clean black-line drawing on pure white background with line hierarchy: heavier outer silhouette, medium major structure, thinner internal detail lines.

The control line must preserve:

- original silhouette, body proportions, stance, and wheelbase
- wheel centers, tire size, wheel arch relationship, and visible wheel design
- front/rear fascia, lamps, grille, intakes, vents, sensors, and plate block
- hood, roofline, beltline, underbody, mirrors, pillars, window shapes, trim, door seams, panel gaps
- original camera angle, perspective, crop, vehicle position, and scale

Reject and regenerate the control line if it becomes sketchy, illustrative, simplified, shaded, colored, over-cleaned, redesigned, or compositionally different.

Use hybrid external SD/ControlNet/Liblib preprocessing only when the default image-to-image/Codex-style control image cannot preserve strict structure. Even then, final rendering should still follow this skill's role separation and quality gates.

## Quality Gates

Treat the output as failed when any Level-1 item fails.

**Level 1: structure gates**

- Front/rear fascia remains the source vehicle.
- Wheelbase, wheel centers, stance, tire size, and wheel arch relation do not move.
- Wheel spoke design remains source-consistent.
- Lamp shapes, DRL signatures, grille/openings, plate block, sensors, and vents remain source-consistent.
- A/B/C pillars, roofline, window boundaries, mirror placement, trim, door seams, and panel gaps remain source-consistent.
- Crop, perspective, focal-length feel, vehicle angle, and scale follow the selected source/reference decision.

**Level 2: requested style gates**

- Paint hue, saturation, brightness, metallic/pearl behavior, gloss, highlight bands, and shadow color match the chosen profile.
- Paint brightness distribution follows the calibrated reference ranges for dark shadows, midtones, main highlights, and brightest accent highlights.
- Lighting recipe matches the reference: upper softbox, glass darkness, mid-body highlight, lower-body shading, rim light, and contrast.
- No source glass pixel noise, checkerboard remnants, dirty smears, cloudy patches, or busy source reflections are inherited into windshield or side glass interiors.
- Rendering remains sharp enough for lamps, grille, wheels, panel gaps, and edges.

**Level 3: background and artifact gates**

- If green background is requested, it is exact solid `#00FF00` / `RGB(0,255,0)` edge-to-edge as a flat 2D compositing color plate.
- No green spill, green reflection, floor texture, horizon, cyclorama, lit green room, ground plane, ground reflection streaks, or wavy reflected floor lines.
- No readable text, watermarks, new logos, new badges, or plate writing unless explicitly requested.

## Default Parameters

Use these defaults unless a selected profile overrides them.

- `structure_priority`: very high
- `style_strength`: medium-low
- `candidate_count`: 4 single / 2 batch
- `background`: exact solid green `#00FF00` when cutout is requested
- `shadow`: soft neutral contact shadow only, under tires and chassis, blurred and feathered
- `silver_paint_hsb`: H=216, S=10, medium-light brightness about half a stop darker than bright white
- `reflections`: neutral cool gray/black studio bands only
- `retry_rule`: restart from original `SOURCE_IMAGE + CONTROL_LINE_IMAGE + STYLE_REFERENCE_IMAGE`

## Resource Loading

- Load `references/analysis-worksheet.md` when analyzing a new source/style pair or auditing output.
- Load `references/paint-calibration.md` when a reference image should define consistent paint brightness, highlight, and shadow ranges.
- Load `references/parameter-profiles.md` before choosing generation settings.
- Load `references/control-line-prompt.md` when generating or regenerating the source-derived control line.
- Load `references/prompt-template.md` only when writing the line-control or final render prompt.
- Load `references/failure-recovery.md` only after a candidate fails or when planning a retry strategy.
- Load `references/job-record-template.md` before production or batch work, and update it after candidate review.
