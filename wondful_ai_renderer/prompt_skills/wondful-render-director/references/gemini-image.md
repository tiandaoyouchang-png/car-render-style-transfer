# Gemini / Nano Banana target profile

Target Antigravity's generate_image tool, not the Gemini/Claude model running the surrounding agent.
The documented tool exposes Prompt, ImageName and optional ImagePaths. Do not invent an independent
image-model selector, control strength, seed, diffusion steps or explicit API-only mask arguments.

For polish, write a connected Chinese scene/appearance narrative instead of a keyword pile: describe
how the chosen environment lights the product, what that implies for highlights, shadows and glass,
and how materials, color grade and photographic finish fit that same illumination. Use positive,
concrete replacement descriptions; keep exclusions brief and unambiguous.

For internal rendering, attach the supplied images through ImagePaths and explain each source's role.
Describe the desired transformation on the edit canvas while preserving supplied geometry. Do not
collage unrelated reference compositions or make the product retain lighting from another photo.
Keep exact requested identity/text explicit. Do not add camera coordinates, lens or scene layout
prose to the visible appearance narrative. No assumption that all Gemini API controls are available
through the narrower CLI tool. Capability output takes precedence over model names in documentation.
