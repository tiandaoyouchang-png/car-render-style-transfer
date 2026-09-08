"""Main-thread Text Editor bridge. Scene.prompt remains the only render input."""
from dataclasses import dataclass

import bpy


@dataclass
class PromptBinding:
    scene: object
    text: object
    last_value: str


_BINDINGS = {}
_SYNCING = False
_AREA_SESSIONS = {}


def reconcile_values(previous, canonical, editor):
    """Return the new canonical value and any concurrent editor draft to preserve."""
    if canonical != previous:
        return canonical, editor if editor != previous and editor != canonical else None
    return editor, None


def _write_text(text, value):
    if text.as_string() != value:
        text.clear()
        text.write(value)


def sync_prompt_editors(props=None):
    global _SYNCING
    if _SYNCING:
        return
    _SYNCING = True
    try:
        for key, binding in list(_BINDINGS.items()):
            try:
                settings = binding.scene.wondful_ai
                if props is not None and settings != props:
                    continue
                value, backup = reconcile_values(
                    binding.last_value, settings.prompt or "", binding.text.as_string(),
                )
                if backup is not None:
                    recovery = bpy.data.texts.new("Wondful Prompt · 编辑备份")
                    recovery.write(backup)
                    recovery.use_fake_user = True
                    settings.prompt_notice = "检测到同时修改，编辑草稿已保存在 Text Editor 的“编辑备份”中。"
                binding.last_value = value  # update before invoking RNA callbacks
                if settings.prompt != value:
                    settings.prompt = value
                _write_text(binding.text, value)
            except (ReferenceError, AttributeError):
                _BINDINGS.pop(key, None)
    finally:
        _SYNCING = False


def _visible_texts():
    return [area.spaces.active.text
            for win in bpy.context.window_manager.windows
            for area in win.screen.areas if area.type == "TEXT_EDITOR"]


def _sync_timer():
    sync_prompt_editors()
    visible = _visible_texts()
    for key, binding in list(_BINDINGS.items()):
        if binding.text not in visible:
            _BINDINGS.pop(key, None)
    return 0.25 if _BINDINGS else None


def ensure_prompt_timer():
    if not bpy.app.timers.is_registered(_sync_timer):
        bpy.app.timers.register(_sync_timer, first_interval=0.25)


def bind_prompt_text(scene):
    sync_prompt_editors(scene.wondful_ai)
    key = scene.as_pointer()
    binding = _BINDINGS.get(key)
    if binding is not None:
        return binding.text
    # Never reuse or clear a user-owned Text datablock, even with the same name.
    text = bpy.data.texts.new(f"Wondful Prompt · {scene.name}")
    text.write(scene.wondful_ai.prompt or "")
    _BINDINGS[key] = PromptBinding(scene, text, scene.wondful_ai.prompt or "")
    return text


def reset_prompt_editors(*, flush=False):
    for record in list(_AREA_SESSIONS.values()):
        try:
            close_prompt_area(record["area"], flush=flush)
        except (ReferenceError, AttributeError):
            pass
    _AREA_SESSIONS.clear()
    if flush:
        sync_prompt_editors()
    if bpy.app.timers.is_registered(_sync_timer):
        bpy.app.timers.unregister(_sync_timer)
    _BINDINGS.clear()


def open_prompt_in_area(context):
    """Use the existing area; creating a new OS window is not required."""
    area = context.area
    if area is None or context.window is None:
        raise RuntimeError("请在 Blender 窗口中打开提示词编辑器。")
    key = area.as_pointer()
    record = _AREA_SESSIONS.get(key)
    if record is not None:
        if record["scene"] == context.scene and area.type == "TEXT_EDITOR":
            ensure_prompt_timer()
            return
        close_prompt_area(area)
    text = bind_prompt_text(context.scene)
    record = {"area": area, "scene": context.scene, "text": text,
              "type": area.type, "ui_type": getattr(area, "ui_type", None),
              "previous_text": getattr(area.spaces.active, "text", None),
              "previous_flags": {key: getattr(area.spaces.active, key) for key in
                  ("show_word_wrap", "show_line_numbers", "show_syntax_highlight", "show_region_header")
                  if area.type == "TEXT_EDITOR" and hasattr(area.spaces.active, key)}}
    _AREA_SESSIONS[key] = record
    try:
        area.type = "TEXT_EDITOR"
        space = area.spaces.active
        space.text = text
        space.show_word_wrap = True
        space.show_line_numbers = False
        space.show_syntax_highlight = False
        if hasattr(space, "show_region_header"):
            space.show_region_header = True
        ensure_prompt_timer()
        area.tag_redraw()
    except Exception:
        close_prompt_area(area)
        raise


def close_prompt_area(area, *, flush=True):
    record = _AREA_SESSIONS.pop(area.as_pointer(), None)
    if record is None:
        return False
    if flush:
        sync_prompt_editors()
    if area.type == "TEXT_EDITOR":
        area.type = record["type"]
        if record["ui_type"] is not None:
            area.ui_type = record["ui_type"]
        if record["type"] == "TEXT_EDITOR":
            area.spaces.active.text = record["previous_text"]
            for key, value in record["previous_flags"].items():
                setattr(area.spaces.active, key, value)
        area.tag_redraw()
    return True


def draw_prompt_editor_header(self, context):
    if context.area and context.area.as_pointer() in _AREA_SESSIONS:
        row = self.layout.row(align=True)
        row.operator("wondful.close_prompt_text_editor", text="完成编辑 · 返回渲染", icon="BACK")
