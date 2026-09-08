# Evaluation and release gates

Use the same Blender camera, product collection and source brief for A/B prompt tests. Compare a
plain baseline with this director for both providers separately. Include broad soft studio light,
bright outdoor diffuse light and a restrained dark environment, with materially distinct finishes.
Preserve reference hashes, ordered notes, instruction version, actual tool/agent information, prompts,
latencies and source/returned images. Do not change geometry or attach different references between A/B.

Score independently: product identity, geometry preservation, reference-style agreement, material
plausibility, unified illumination, artifact rate and time/cost. Randomize review order and judge more
than one output per setting when the user approves the additional requests. Never equate star count,
a model's self-rating, hash correctness or static tests with an improvement in visual quality.

Gate installation on compile/import tests, input mapping and auth state tests; gate production use
on real Blender UI tests, real CLI OAuth and end-to-end image tests. Do not generate paid samples
silently. The current pack is an informed baseline; report whether live visual A/B tests ran.
