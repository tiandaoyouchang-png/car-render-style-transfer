# Analysis Worksheet

Fill this before writing the generation prompt. Keep each field concise and concrete. The worksheet is a control surface for reproducibility, not prose.

## Job Card

- **Job ID / car ID**:
- **Mode**: single / batch
- **Selected profile**: fidelity-lock / balanced-style / style-forward / strict-green-cutout / batch-silver-green
- **SOURCE_IMAGE role**:
- **CONTROL_LINE_IMAGE status**: not created / created / rejected / accepted
- **STYLE_REFERENCE_IMAGE role**:
- **Output aspect ratio**:
- **Candidate count**:
- **Retry number**: R0 / R1 / R2 / R3
- **Changed parameter since last retry**:

## Source Lock Facts

Write 5-8 facts that must survive. These become the `SOURCE LOCK FACTS` section of the prompt.

- **Vehicle type and proportion**:
- **Silhouette / crop / camera**:
- **Fascia and body openings**:
- **Lamp design**:
- **Wheel design and wheel placement**:
- **Window / pillar / glass layout**:
- **Trim / mirrors / roof modules / handles / panel gaps**:
- **Most fragile source details**:

## Style Recipe Facts

Write only style facts that may transfer. Do not include reference-vehicle geometry.

- **Render style**:
- **Paint hue / saturation / brightness**:
- **Paint material behavior**:
- **Highlight recipe**:
- **Shadow and glass recipe**:
- **Reflection recipe**:
- **Camera/composition facts selected for transfer, if any**:
- **Reference facts that must not transfer**:

## Paint Luminance Calibration

Fill this when paint consistency matters. Use `references/paint-calibration.md`.

- **Reference calibration source**:
- **Dark painted shadows HSB_B / L***:
- **Controlled midtones HSB_B / L***:
- **Main silver highlights HSB_B / L***:
- **Brightest accent highlights HSB_B / L***:
- **Where highlights should appear on this source car**:
- **Where dark painted shadows should remain on this source car**:

## Prompt Decisions

- **Composition mode**: keep source / match reference scale only / match selected reference camera feel
- **Camera mode**: keep source / slight reference feel / explicit reference focal-length feel
- **Paint target**:
- **Lighting strength**: low / medium / high
- **Gloss strength**: low / medium / high
- **Structure priority**: high / very high / maximum
- **Style strength**: low / medium-low / medium / high
- **Background block**: pure green / reference studio / neutral cutout-ready
- **Green-background strictness**: off / normal / strict

## Control-Line Audit

Accept only if all required items remain source-consistent.

- **Silhouette and proportions**: pass / fail
- **Wheel centers and stance**: pass / fail
- **Wheel design outline**: pass / fail
- **Fascia / grille / openings**: pass / fail
- **Lamp shapes**: pass / fail
- **Window / pillars / mirrors**: pass / fail
- **Panel gaps / character lines**: pass / fail
- **Perspective / crop / vehicle scale**: pass / fail
- **Line style is CAD-like, not sketchy or illustrative**: pass / fail
- **Decision**: accept / regenerate control line

## Output Quality Gates

Mark failed items before deciding whether to accept or retry.

### Level 1: Structure Gates

- **Vehicle identity**: pass / fail
- **Front/rear fascia**: pass / fail
- **Wheelbase / wheel centers / stance**: pass / fail
- **Wheel design**: pass / fail
- **Lamp shapes and signatures**: pass / fail
- **Grille / intakes / sensors / vents / plate block**: pass / fail
- **A/B/C pillars and glass boundaries**: pass / fail
- **Silhouette / roofline / underbody / crop**: pass / fail
- **Camera / perspective / focal-length feel**: pass / fail
- **Vehicle scale and position**: pass / fail

### Level 2: Style Gates

- **Paint hue / saturation / brightness**: pass / fail
- **Paint luminance range consistency**: pass / fail
- **Paint material and gloss**: pass / fail
- **Highlight placement and softness**: pass / fail
- **Side-profile contrast and local highlight brightness**: pass / fail
- **Glass darkness / lower-body shading / rim light**: pass / fail
- **Glass continuity, no stripes/blocks/noise**: pass / fail
- **A-pillar and windshield-edge cleanliness**: pass / fail
- **Glass material override, no source glass texture inherited**: pass / fail
- **Render sharpness and CGI polish**: pass / fail

### Level 3: Background / Artifact Gates

- **Requested background**: pass / fail
- **Contact shadow**: pass / fail
- **No green spill or green reflection**: pass / fail
- **No ground reflections / floor streaks / wavy reflected lines**: pass / fail
- **No readable text / watermark / new logos / new badges**: pass / fail

## Failure Triage

- **Primary failure type**: structure / style / paint / background / sharpness / composition / mixed
- **Rejected candidate IDs**:
- **Accepted candidate ID, if any**:
- **Next action**: accept / retry same profile with one parameter change / switch profile / regenerate control line / use hybrid control
- **One parameter group to change next**:
- **Instruction to remove from next prompt, if contradictory**:

## Task Artifact Record Summary

Keep this short. Put the full production log in `references/job-record-template.md` format.

- **Job record path**:
- **Source asset ID/path**:
- **Style reference asset ID/path**:
- **Accepted control line ID/path**:
- **Selected profile**:
- **Control-line prompt version**:
- **Render prompt version**:
- **Accepted result ID/path**:
- **Final status**: accepted / retry needed / blocked
