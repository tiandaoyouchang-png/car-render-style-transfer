# Wondful AI Renderer 3.1.0 - Auth bridge and model-adapted art direction

Based on the user's uploaded 3.0.9 source, preserving its shape-only product references and environment-led relighting policy.

## Authentication

- Split passive executable/version detection from explicit connection validation. Detection does not start a model task or browser authentication.
- Keep a managed official agy process alive for the browser/code round trip. Read incremental stdout/stderr, including code prompts without a newline. Submit authorization code ONLY to that originating process's stdin.
- Use the platform's script(1) PTY on macOS/Linux. Normal inference and login use the same executable/environment transport. Windows retains a pipe fallback, not a claimed ConPTY implementation.
- Require a successful terminal CLI result. After new authorization, verify saved-credential reuse in a fresh process. Browser success alone is not enough.
- Add waiting-for-browser/code/verification states, cancel, allowlisted browser URL and terminal-initialization fallback. Never fake SSH variables or bypass tool permissions.
- Keep the code in WindowManager transient state; clear on submission, cancellation, save, file load and unregister. Diagnostics redact URLs/codes/token-shaped data.
- Separate advertised generate_image availability from account verification. Neither guarantees permission to generate an image.

## Model adaptation and original embedded skill

- Add versioned common art-direction guidance plus separate OpenAI-image and Gemini-image profiles.
- Deterministically inject only the common rules and the selected profile; do not rely on automatic CLI skill discovery or install anything globally.
- Distinguish the CLI reasoning model from the platform-managed image tool. Store actual image model as unknown when the CLI has not reported it.
- Invalidate a generated prompt on provider/model/profile change. Preserve visible manual content and require explicit adaptation.
- Cache style analysis by image bytes/order, per-reference notes, provider, reasoning-model request and profile hash.
- Give each AGY analysis call its own staged-input directory.

## Workflow and safety

- Preserve reference-first workflow, user review before image generation, one canonical prompt and one generation in standard mode.
- Put output selection before generation; preflight directory writability before an expensive request.
- Correct unsaved .blend output fallback (an empty Path was previously treated as a saved-file location).
- Put task stage and explicitly estimated percentage in the action area. Show one actionable blocking reason.
- Keep authenticated controls in settings; make Connect accessible when logged out even when account details are collapsed.
- Remove truncated fallback prompt preview. Unsupported sidebar versions still use the real Text Editor fallback, not fake row inputs.
- Fix sanitizer fallback that could return the original geometry-only text after filtering everything out.

## Verification status

118 automated tests pass. Live Google OAuth, native macOS Keychain, Windows interactive auth, Blender UI/GPU integration and image-quality A/B comparisons are NOT verified in this build environment.
