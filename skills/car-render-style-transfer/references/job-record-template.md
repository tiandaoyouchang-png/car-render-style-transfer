# Job Record Template

Use one job record per source car. For batch work, name records with:

```text
[batch_id]_[source_id]_job-record.yaml
```

The job record is a production log and audit trail. Do not paste the full job record into the generation prompt; use it to track inputs, prompts, candidates, failures, and accepted outputs.

```yaml
job_id:
batch_id:
source_id:
mode: single # single | batch
created_at:
updated_at:
operator:

input_record:
  source:
    file:
    asset_id:
    version:
    crop_status:
    aspect_ratio:
    notes:
  style_reference:
    file:
    asset_id:
    version:
    crop_status:
    aspect_ratio:
    notes:
  control_line:
    file:
    asset_id:
    version:
    source_derived: true
    accepted: false
    notes:

analysis_record:
  worksheet_file:
  source_lock_summary:
  style_recipe_summary:
  prompt_decisions_summary:

generation_record:
  retry_number: 0
  profile:
  control_line_prompt_version: control-line-cad-v1
  render_prompt_version: render-template-v2.1
  candidate_count:
  background_mode:
  paint_target:
  structure_priority:
  style_strength:
  lighting_strength:
  gloss_strength:
  changed_parameter_group:
  final_render_prompt_file:
  final_render_prompt_text:

candidate_record:
  candidate_ids: []
  candidate_files: []
  accepted_candidate_id:
  accepted_result_file:
  rejected_candidates:
    - candidate_id:
      file:
      failed_quality_gates: []
      failure_category:
      failure_notes:

quality_gate_results:
  level_1_structure:
    vehicle_identity:
    fascia:
    wheelbase_wheel_centers_stance:
    wheel_design:
    lamp_shapes:
    grille_openings_sensors_plate_block:
    pillars_glass_boundaries:
    silhouette_roofline_underbody_crop:
    camera_perspective_focal_length:
    vehicle_scale_position:
  level_2_style:
    paint_hue_saturation_brightness:
    paint_material_gloss:
    highlight_placement_softness:
    side_profile_contrast_local_highlights:
    glass_lower_body_rim_light:
    glass_continuity_no_stripes_blocks_noise:
    a_pillar_windshield_edge_cleanliness:
    glass_material_override_no_source_texture:
    render_sharpness_cgi_polish:
  level_3_background_artifacts:
    requested_background:
    contact_shadow:
    no_green_spill_or_reflection:
    no_ground_reflections_or_floor_streaks:
    no_text_watermark_new_logo_badge:

failure_recovery:
  failure_category:
  failed_quality_gates: []
  next_retry_action:
  next_changed_parameter_group:
  instruction_to_remove:
  use_hybrid_control: false

final_status: pending # pending | accepted | retry_needed | blocked
final_notes:
```
