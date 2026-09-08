# OpenAI ImageGen target profile

Target the built-in Codex image generation/editing tool, not the Codex reasoning model name.
For polish, organize the Chinese prose as primary requested appearance change, subject identity,
material response, lighting/reflections, color/finish and a short set of exclusions. Preserve detailed
user text instead of inflating it. Use concrete edit verbs and name what changes versus what remains.

For the internal render brief, use short labelled sections: EDIT TASK, REFERENCE ROLES, APPEARANCE,
PRESERVE, OUTPUT. Describe the camera image as the canvas and other images by role, not all as edit
targets. Confirm image inputs are visually available to the tool. Keep exact text only when requested.
Never emit fictional --style/--iw/seed/ControlNet parameters or use another API automatically.

Do not put camera positions, angles, lens lengths or crop decisions in the visible prompt. Keep
preservation instructions in the internal reference contract. Tool parameters are capability-gated:
a labelled mask reference is not equivalent to an explicitly supported mask parameter.
The exact image model may be opaque to Codex; do not claim that --model selects GPT Image.
