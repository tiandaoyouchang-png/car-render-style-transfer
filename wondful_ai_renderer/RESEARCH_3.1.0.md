# Wondful AI Renderer 3.1.0 - Research and engineering decisions

Reviewed: 2026-09-05. Authoritative input: the user-uploaded 3.0.9 source and install archives.

## 结论摘要

建议内置一个专用的商业渲染提示词 Skill，但不直接整包照搬前端设计 Skill。
共用参考图职责和商业画质规则，按生图平台加载不同编写规则。
没有可核实的统一评测能证明某个设计 Skill 是“美商最高”。展示图和星数不能替代同条件生图对比。

AGY 的确定问题是登录交互和连接验证没有闭环，不能仅靠修改“已登录”标签解决。
新版已实现原进程授权码提交和新进程复用验证，但尚未完成真实 Google OAuth 实机验证。

原始目标保持不变：Blender 控制结构，AI 生成外观；润色完成写回同一输入框，用户确认后再生图。
当前多图条件不等于真正的 ControlNet，也不保证像素级一致。

The detailed engineering record below is in English so it can be consumed directly by maintainers and coding agents. The README and manual acceptance checklist provide the Chinese operating instructions.

## 1. Evidence levels and product contract

This report separates three kinds of information:

- **Source-audited facts:** behavior actually found in the uploaded 3.0.9 code, or changes present in this 3.1.0 working tree.
- **External research:** current official documentation and repository-authored descriptions linked below. Issue reports are reports, not proof that the same defect affects this user's machine.
- **Design recommendations:** engineering decisions and tests to perform; not measured aesthetic improvements.

The original MD describes image-aware prompt writing, role-separated references, scene structure owned by the 3D application, and manual review before generation. Later user decisions replace C4D/API-key rendering with Blender and CLI OAuth. The uploaded 3.0.9 code is more recent and explicitly treats product references as identity/shape only, with environment-led relighting. This release retains that policy rather than silently restoring the original document's product-color/material defaults.

## 2. AGY authentication: what was wrong

### Findings in uploaded 3.0.9

`WONDFUL_OT_antigravity_check` called a live model probe. It was not merely an installation check. The subprocess wrapper closed standard input with DEVNULL, so a browser flow returning an authorization code had no live input channel in Blender. `WONDFUL_OT_antigravity_login` opened an external terminal without an owned login process or a completion watcher.

These are sufficient implementation gaps to explain a silent plugin after browser authorization. They do **not** establish whether this user's particular CLI also has a keyring, proxy, browser-loopback or credential-persistence problem.

### What current official sources support

The installation guide describes OS keyring reuse and a manual browser/code loop in remote situations [S1]. A code belongs to the CLI session that initiated authorization. The headless guide distinguishes response stdout from diagnostic/auth stderr, describes cached credentials, and documents terminal JSON status plus tool availability events [S2].

The official issue tracker also contains a macOS report where browser login appears successful but the CLI never becomes authenticated [S3]. Treat that as a possible upstream failure class, not a diagnosis for this user. Do not respond to it by forcing the plugin into a false LOGGED_IN state.

### Implemented connection design

```
Detect installation (path/version only; no model request)
          |
Connect / verify (explicit minimal text request)
          |
Official agy owned process + POSIX PTY where available
          |
Browser authorization OR code prompt in that same process
          |
Code field appears ONLY while the process requests a code
          |
CLI terminal SUCCESS and exit 0
          |
If authorization occurred: a fresh process must reuse credentials
          |
Connected / actionable failure, not browser-only success
```

The bridge does not implement Google's OAuth exchange, read token files, extract a Keychain secret, change client IDs, fake SSH variables or disable CLI permission checks. It forwards user-provided input to the originating process. A code from a previously closed terminal cannot safely be submitted to a new login.

A canceled/closed session rejects late codes and terminates only its own process group. The code is a transient WindowManager property, not a saved Scene property. It is cleared on submission and lifecycle cleanup. The plugin's diagnostics redact it. The official CLI remains responsible for its own credential storage.

Normal AGY inference uses the same selected executable/environment transport. If authentication is unexpectedly requested during image generation, the task fails instead of silently waiting for a code or restarting a paid generation. First-launch theme/trust prompts are routed to a terminal-initialization fallback requiring the user's normal approval.

**Limitations:** only the fake CLI bridge ran end-to-end in Linux. macOS command construction was tested, but live Keychain/browser behavior was not. Windows has a pipe fallback, not ConPTY. Connection verification normally uses one small text task; new authentication can require a second reuse-check task. These requests may consume platform quota. Successful connection does not prove that generate_image is authorized or that a usable image will be returned.

## 3. Model adaptation must target the image tool, not just the agent label

Three entities must be separated:

| Entity | Example in this plugin | Purpose |
|---|---|---|
| Provider/CLI | Codex or Antigravity | Authentication, files, agent and tool execution |
| Reasoning model | The value passed to `--model` | Understand references and write/execute instructions |
| Image tool/backend | Built-in image generation | Produce the bitmap |

Antigravity's model documentation currently names Nano Banana 2 as an additional image-generation tool model and says it is not customizable [S4]. Selecting another reasoning model does not prove that the image backend changed. The hook schema exposes Prompt, ImageName and ImagePaths for generate_image [S5]; API-only options should not be invented for that tool.

The plugin records the selected reasoning model, target prompt profile, pack version and hash. If the runtime does not report the actual image model, the metadata retains `null` rather than claiming a guessed model. Future backend changes require rechecking official runtime behavior and the profile pack.

### Two implemented prompt profiles

**OpenAI ImageGen/Codex profile.** Use an explicit edit task, clearly distinguish the edit canvas from reference images, express requested appearance changes and preserve the existing identity/geometry at the task level. Keep a compact production brief, not an uncontrolled expansion of the user's request. OpenAI's official image skill documents role labels, edit invariants, deliberate augmentation and built-in-vs-API-fallback distinctions [S6].

**Gemini image/Antigravity profile.** Use a coherent description connecting the environment, key/fill illumination, reflected surroundings and material response. Keep image roles explicit. Google's image guidance emphasizes descriptive scene instructions rather than disconnected keywords [S7]. The plugin translates that principle into appearance-only art direction; it does not add a new camera or layout.

Both profiles intentionally share the product contract and reference boundaries. Different wording is not a magic quality switch. The hypothesis is that clearer model-appropriate task expression improves consistency; its size and quality impact require controlled image tests.

Switching provider, reasoning-model request or profile version invalidates an AI-generated prompt. The draft is preserved and the user explicitly chooses adaptation. A first, manually authored prompt is not forced through AI polish. Model adaptation never auto-starts image generation.

## 4. Research on high-aesthetic design skills

There is no verified universal ranking for 'highest aesthetic taste' across these projects. Their screenshots, examples and popularity are not a common controlled benchmark. The useful question for Wondful is whether a skill improves image-role fidelity, lighting/material coherence, repeatability and UI clarity without introducing a different product goal.

| Source | What its own repository supports | Fit for Wondful | Decision |
|---|---|---|---|
| OpenAI official imagegen [S6] | Image generation/edit workflow, input roles, invariants, review and artifact handling | Closest direct match to an image-rendering pipeline | Adapt the principles into an original provider profile; do not enable its API-key fallback |
| Anthropic frontend-design [S8] | Deliberate visual direction and frontend implementation rather than generic UI | Useful critique of the addon workflow, not an automotive-render instruction set | Borrow the evaluation questions, not HTML/CSS or new-layout directives |
| pbakaus/impeccable [S9] | Design language plus critique/audit/refinement commands for AI design workflows | Strong fit for hierarchy, errors, onboarding and simplifying UI states | Use as a UI review reference; do not inject the entire package into every image task |
| Leonxlnx/taste-skill [S10] | Opinionated anti-generic frontend design guidance | Useful for intentional choices and avoiding decorative clutter | Keep relevant judgment principles; exclude frontend-specific structure, typography and animation instructions |
| wuyoscar/GPT-Image2-Skill [S11] | Prompt gallery/library, skill and CLI for image work | Useful source of varied visual cases and evaluation examples | Treat as a reference library, not a claim that every example transfers to an existing Blender camera |

No third-party skill code was copied wholesale into the plugin. The embedded rules are original Wondful instructions based on the user's contract and the documented principles. Any later direct reuse of source/assets must separately check its license and retain notices. Repository stars were deliberately not used as an aesthetic score.

## 5. Embedded skill: yes, but as a deterministic instruction pack

The release includes `prompt_skills/wondful-render-director/` with:

```
SKILL.md
agents/openai.yaml
references/commercial.md
references/openai-image.md
references/gemini-image.md
references/evaluation.md
references/sources.md
```

`prompt_profiles.py` deterministically reads the entrypoint, common commercial rules and exactly one provider profile. This avoids relying on a CLI's opportunistic skill discovery. It also avoids putting a large frontend-design knowledge base into every call. Nothing is installed globally and no new paid API is required.

The commercial rules prefer specific, coherent light/material behavior over strings of 'cinematic, 8K, masterpiece'. They cover controlled highlight rolloff, readable shadow-side surfaces, paint/metal/glass/rubber separation, environment-consistent reflections, contact shadows and avoiding invented logos/props. Reference-image text is treated as content, not as instructions.

This is instruction engineering, **not training or fine-tuning**. It cannot add unavailable image-tool parameters, improve an inaccessible model's weights, guarantee identity/composition or fix broken reference delivery by itself.

### Cache with evidence, not 'first reference forever'

A cached style analysis is valid only for the exact ordered image bytes and reference notes, provider, reasoning-model request and instruction-pack hash. Unchanged references can skip repeated style-only analysis. New style bytes, same-path file replacement, changed notes, order or target profile invalidate the cache. Every AGY analysis call receives a unique staging directory; stages do not reuse one ambiguous set of filenames.

The final appearance prompt is still generated from the current brief and valid analysis, returned to the user's editor, and manually approved. It is not silently baked into an invisible alternative prompt.

## 6. Additional improvements delivered

- Output directory selection precedes the render action. A write preflight occurs before the expensive remote task; fix the empty-unsaved-blend Path case.
- Preserve standard mode's single generation. Strict-mode audit/repair remains an explicit choice. No automatic cross-provider fallback or unexpected second image call.
- Keep verified account controls inside settings and one obvious Connect action while unverified. Code entry is contextual, not permanently exposed.
- Show operation phase and explicitly estimated progress in its action area; distinguish waiting for authorization from image generation.
- Show one actionable blocking reason. Keep error information readable and offer a redacted diagnostic copy instead of truncating it.
- Keep references and per-image notes above prompt generation. Preserve one canonical full prompt and the real Text Editor fallback when a native sidebar textbox is unavailable.
- Retain 3.0.9's reference-role, background/subject relighting, non-destructive workspace and artifact-validation work. No unrelated scene rewrite was introduced.

## 7. High-priority next work (not falsely claimed delivered)

**First: live auth and input-delivery verification.** Test on the user's exact Mac/Blender/agy build. Record launcher path/version and whether browser-only or manual-code authorization actually occurs. Inspect redacted diagnostics, not raw tokens. Verify image capabilities with a user-initiated render, not automatic paid probes.

**Second: controlled quality tests.** Use the same scene, camera, geometry, refs/notes and output size. Compare legacy and adapted prompts within each provider. Repeat each case several times and blind the review order. Built-in tools may not expose a seed, so report stochastic variation rather than pretending pairwise determinism. Include an indoor glossy vehicle, outdoor environment relighting, dark paint, transparent glass, a non-car product and a clearly different A-to-B style switch.

Track geometry drift and identity separately from appearance. Useful measurements include normalized center/bounding-box displacement, wheel-anchor residuals where corresponding points are actually identified, material separation, illumination consistency, unsupported additions, user edit effort, failure rate and end-to-end latency. A generated-image silhouette or keypoint detector needs its own confidence validation; the source mask alone cannot measure output accuracy.

**Third: geometry precision.** The current packet consists of additional visual conditions, not a native ControlNet conditioning path. More rasters are not automatically better; test mask/depth/normal/silhouette ablations to avoid noisy or conflicting references. For a future strict pixel-preservation mode, consider retaining deterministic product pixels or rerendering known 3D geometry and compositing generated surroundings. Such a mode changes which appearance degrees of freedom remain and needs its own shadow/reflection/occlusion design. A dedicated conditioning backend would require separate capability and deployment decisions, and is not silently added here.

## 8. Primary sources

[S1] Google Antigravity CLI, Installation & auth: https://antigravity.google/docs/cli/install

[S2] Google Antigravity CLI, Headless mode: https://antigravity.google/docs/cli/headless

[S3] Google Antigravity CLI issue #787, browser/CLI authentication report (user report, not a confirmed diagnosis for cc): https://github.com/google-antigravity/antigravity-cli/issues/787

[S4] Google Antigravity, Models: https://antigravity.google/docs/models

[S5] Google Antigravity, Hooks / generate_image tool schema: https://antigravity.google/docs/hooks

[S6] OpenAI official image generation skill: https://github.com/openai/skills/blob/main/skills/.system/imagegen/SKILL.md
Prompting reference: https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/imagegen/references/prompting.md

[S7] Google AI for Developers, Gemini image generation: https://ai.google.dev/gemini-api/docs/image-generation

[S8] Anthropic frontend-design skill: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md

[S9] Impeccable, author's repository: https://github.com/pbakaus/impeccable

[S10] Taste-Skill, author's repository: https://github.com/Leonxlnx/taste-skill

[S11] GPT-Image2-Skill, author's repository: https://github.com/wuyoscar/GPT-Image2-Skill

## 9. Delivery status

Implementation and 118 offline tests are complete in 3.1.0. Live authentication, real Blender UI/GPU behavior and aesthetic/composition A/B tests are still acceptance items. The source archive includes tests and build scripts so the next maintainer can reproduce local checks rather than relying on previous chat claims.
