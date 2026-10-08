from __future__ import annotations

from pathlib import Path

from textwrap import wrap
import unicodedata

import bpy
from bpy.types import Panel, UIList

from .properties import MAX_REFERENCES_PER_KIND
from . import prompt_profiles
from .prompt_engine import needs_reference_policy_refresh
from .viewport_capture import camera_output_dimensions
from .operators import render_variant_count


def _prefs(context):
    return context.preferences.addons[__package__].preferences


def _disclosure(row, props, attr, label, icon="NONE", suffix=""):
    opened = bool(getattr(props, attr))
    row.prop(props, attr, text="", icon="TRIA_DOWN" if opened else "TRIA_RIGHT", emboss=False)
    row.label(text=f"{label}{suffix}", icon=icon)
    return opened


PROMPT_EDITOR_VISIBLE_ROWS = 6


def _prompt_display_lines(text, columns=36):
    """Wrap CJK and Latin display cells without modifying the canonical prompt."""
    result = []
    for paragraph in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line, width = "", 0
        for char in paragraph:
            cells = 0 if unicodedata.combining(char) else (2 if unicodedata.east_asian_width(char) in "WF" else 1)
            if line and width + cells > columns:
                result.append(line)
                line, width = "", 0
            line += char
            width += cells
        result.append(line)
    return result


def _prompt_char_count(text: str) -> int:
    """Count visible prompt characters; line breaks are not counted as 字."""
    return len((text or "").replace("\r", "").replace("\n", ""))


def _draw_prompt_editor(layout, props, columns=36):
    """Draw one canonical prompt editor.

    Prefer Blender's native multi-line textbox whenever the running build exposes
    it (feature detection, not a hard version check). Older Blender builds do not
    provide an inline multi-line RNA editor in panels, so never fake one with
    per-line StringProperty fields: expose a single editable StringProperty and
    a full Text Editor in the current area with a return button.
    """
    expanded = bool(getattr(props, "prompt_expanded", False))
    lines = _prompt_display_lines(props.prompt, columns)
    if callable(getattr(layout, "textbox", None)):
        try:
            layout.textbox(
                props, "prompt",
                initial_visible_lines=max(12, min(30, len(lines))) if expanded else PROMPT_EDITOR_VISIBLE_ROWS,
                placeholder="输入创意需求，或点击 AI 润色生成完整提示词…",
            )
            return
        except (TypeError, AttributeError):
            # A backport may expose a different signature; keep the panel usable.
            pass

    field = layout.box()
    # Always begin with one real editable field. Both routes edit props.prompt.
    entry = field.row()
    entry.scale_y = 1.4
    entry.prop(props, "prompt", text="")
    if props.prompt:
        preview = field.column(align=True)
        preview.scale_y = 0.95
        visible = lines[:120] if expanded else lines[:PROMPT_EDITOR_VISIBLE_ROWS]
        for line in visible:
            preview.label(text=line or " ")
        if len(lines) > len(visible):
            preview.label(text=f"还有 {len(lines) - len(visible)} 行，" + ("可在完整编辑器中读取" if expanded else "点击展开全文"))
    field.operator("wondful.open_prompt_text_editor", text="编辑完整提示词", icon="GREASEPENCIL")


def _draw_progress_action(row, props, *, active_status: str, idle_text: str, icon: str, operator: str, enabled: bool = True):
    """Use the action button's own slot as its live progress indicator."""
    if props.status == active_status:
        pct = max(0, min(100, int(round(float(props.progress) * 100))))
        phase = getattr(props, "task_phase", "")
        text = f"{phase or idle_text} · 估算 {pct}%"
        row.enabled = False
        if hasattr(row, "progress"):
            row.progress(factor=max(0.0, min(1.0, float(props.progress))), text=text, type="BAR")
        else:
            # Older Blender fallback: slider occupies the same action slot.
            row.prop(props, "progress", text=text, slider=True)
        return None
    row.enabled = bool(enabled)
    return row.operator(operator, text=idle_text, icon=icon)


class WONDFUL_UL_prompt_lines(UIList):
    bl_idname = "WONDFUL_UL_prompt_lines"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "text", text="", emboss=False)


class WONDFUL_UL_reference_items(UIList):
    """Legacy compatibility only; 2.7 renders references as image cards instead."""
    bl_idname = "WONDFUL_UL_reference_items"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        image = getattr(item, "image", None)
        layout.label(text=(image.name if image else "无效图片"), icon="IMAGE_DATA" if image else "ERROR")


def _draw_reference_card(layout, props, item, index, kind):
    card = layout.box()
    split = card.split(factor=0.36)
    preview = split.column(align=True)
    if item.image:
        icon_value = bpy.types.UILayout.icon(item.image)
        preview.template_icon(icon_value=icon_value, scale=5.0)
    else:
        preview.label(text="图片无效", icon="ERROR")

    meta = split.column(align=True)
    if kind == "STYLE":
        primary_text = "主光来源"
        icon0 = "LIGHT_SUN"
    else:
        primary_text = "主参考"
        icon0 = "CHECKMARK"
    if kind == "PRODUCT" and index > 0:
        meta.label(text="未使用（只用第一张）", icon="ERROR")
    else:
        meta.label(text=primary_text if index == 0 else f"辅助 {index + 1}", icon=icon0 if index == 0 else "IMAGE_DATA")
    if item.image:
        name = item.image.name
        meta.label(text=name if len(name) <= 24 else name[:21] + "…")
    meta.prop(item, "instruction", text="造型重点" if kind == "PRODUCT" else "参考什么")
    controls = meta.row(align=True)
    if kind != "PRODUCT":
        up = controls.operator("wondful.move_reference", text="", icon="TRIA_UP")
        up.ref_kind, up.direction, up.item_index = kind, "UP", index
        down = controls.operator("wondful.move_reference", text="", icon="TRIA_DOWN")
        down.ref_kind, down.direction, down.item_index = kind, "DOWN", index
    replace = controls.operator("wondful.replace_reference", text="", icon="FILE_REFRESH")
    replace.ref_kind, replace.item_index = kind, index
    remove = controls.operator("wondful.clear_reference", text="", icon="X")
    remove.ref_kind, remove.item_index = kind, index


def _draw_reference_group(layout, props, title, collection_attr, index_attr, kind, open_attr):
    collection = getattr(props, collection_attr)
    box = layout.box()
    header = box.row(align=True)
    opened = _disclosure(header, props, open_attr, title, suffix=f"  {len(collection)}")
    header.separator()
    replaces = kind in {"STYLE", "PRODUCT"} and bool(collection)
    add_text = "换图" if replaces else "文件"
    add_icon = "FILE_REFRESH" if replaces else "ADD"
    add = header.operator("wondful.load_reference", text=add_text, icon=add_icon)
    add.ref_kind = kind
    paste = header.operator("wondful.paste_reference", text=("替换粘贴" if replaces else "粘贴"))
    paste.ref_kind = kind
    if collection:
        clear_all = header.operator("wondful.clear_all_references", text="", icon="TRASH")
        clear_all.ref_kind = kind
    if not opened:
        return

    if kind == "PRODUCT":
        box.label(text="只用 1 张，建议放三视图（正/侧/后拼成一张）。", icon="INFO")
        box.label(text="仅参考产品造型，不参考原图打光。")
    elif kind == "STYLE":
        box.label(text="决定产品受光、反射、阴影与环境氛围。", icon="LIGHT")
    if not collection:
        empty = box.column(align=True)
        empty.label(text="拖入文件，或复制图片后点“粘贴”", icon="IMAGE_DATA")
        if kind == "STYLE":
            empty.label(text="第一张决定主光，可用箭头调整顺序；最多 8 张。")
        elif kind == "PRODUCT":
            empty.label(text="只放 1 张；再上传会直接替换。")
        else:
            empty.label(text="第一张自动作为主参考；最多 8 张。")
        return

    # The preview and its identity/controls now live in one card. There is no
    # detached name list + selected-image preview anymore.
    for index, item in enumerate(collection):
        _draw_reference_card(box, props, item, index, kind)


class WONDFUL_PT_main(Panel):
    bl_label = "Wondful AI 渲染器 · 3.1.9"
    bl_idname = "WONDFUL_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wondful AI"

    def draw(self, context):
        """3.1.9: four steps on top (连接 / 产品 / 场景 / 生成); everything else in 高级."""
        from .operators import generate_needs_polish
        layout = self.layout
        props = context.scene.wondful_ai
        prefs = _prefs(context)
        busy = props.status in {"AUTHENTICATING", "CLASSIFYING", "POLISHING", "RENDERING", "REFRESHING_MODELS"}

        active_is_antigravity = props.analysis_provider == "ANTIGRAVITY"
        state = props.antigravity_account_state if active_is_antigravity else props.codex_account_state
        account_message = props.antigravity_account_message if active_is_antigravity else props.codex_account_message
        cli_version = props.antigravity_cli_version if active_is_antigravity else props.codex_cli_version
        provider_label = "Antigravity" if active_is_antigravity else "Codex"
        refresh_op = "wondful.antigravity_check" if active_is_antigravity else "wondful.codex_check"
        camera = context.scene.camera
        camera_w, camera_h = camera_output_dimensions(context)

        # ---- ① 连接 -------------------------------------------------------------
        step1 = layout.box()
        head = step1.row(align=True)
        if state == "LOGGED_IN":
            head.label(text=f"① 连接 · {provider_label} 已连接", icon="CHECKMARK")
        else:
            account_text = {
                "UNKNOWN": f"{provider_label} 未检测",
                "NOT_INSTALLED": f"找不到 {provider_label}",
                "LOGGED_OUT": ("Google 未登录" if active_is_antigravity else "ChatGPT 未登录"),
                "ERROR": f"{provider_label} 异常",
            }.get(state, state)
            if active_is_antigravity and props.status == "AUTHENTICATING":
                account_text = "正在连接 Google"
            head.label(text=f"① 连接 · {account_text}", icon="QUESTION" if state == "UNKNOWN" else "ERROR")
            head.operator(refresh_op, text="检测", icon="FILE_REFRESH")
            connect = step1.row(align=True)
            connect.scale_y = 1.2
            connect.enabled = not busy
            if active_is_antigravity:
                connect.operator("wondful.antigravity_terminal", text="Google 登录", icon="USER")
                connect.operator("wondful.antigravity_login", text="验证登录", icon="CHECKMARK")
                step1.label(text="终端和浏览器里登录完，回来点验证登录。")
            else:
                connect.operator("wondful.codex_login", text="使用 ChatGPT 登录", icon="USER")
            if state == "NOT_INSTALLED":
                step1.label(text="已装 Codex 仍找不到？在高级 › 插件偏好设置里填它的路径。", icon="INFO")
            elif account_message:
                step1.label(text=account_message[:90])
        if props.status == "AUTHENTICATING":
            auth = step1.box()
            if active_is_antigravity:
                for line in wrap(props.auth_detail or "正在连接 AGY", width=38):
                    auth.label(text=line)
                if props.auth_has_url:
                    auth.operator("wondful.antigravity_auth_browser", text="打开本次登录页", icon="URL")
                if props.auth_stage == "WAITING_CODE":
                    auth.prop(context.window_manager, "wondful_auth_code", text="授权码")
                    auth.operator("wondful.antigravity_submit_code", text="提交授权码", icon="CHECKMARK")
                auth.operator("wondful.antigravity_auth_cancel", text="取消连接", icon="CANCEL")
            else:
                auth.prop(props, "progress", text="等待浏览器授权", slider=True)

        # ---- ② 产品 -------------------------------------------------------------
        step2 = layout.box()
        step2.label(text="② 产品", icon="OUTLINER_COLLECTION")
        step2.prop(props, "product_collection", text="产品集合")
        if not camera:
            step2.label(text="场景里还没有活动相机", icon="ERROR")
        _draw_reference_group(step2, props, "产品参考（三视图）", "product_images", "product_image_index", "PRODUCT", "ui_show_product_refs")

        # ---- ③ 场景 -------------------------------------------------------------
        step3 = layout.box()
        step3.label(text="③ 场景", icon="WORLD")
        _draw_reference_group(step3, props, "环境参考", "style_images", "style_image_index", "STYLE", "ui_show_style_refs")
        step3.label(text="一句话需求（可留空）：")
        step3.prop(props, "scene_brief", text="")

        # ---- ④ 生成 -------------------------------------------------------------
        imagegen_enabled = prefs.codex_imagegen_enabled if not active_is_antigravity else prefs.antigravity_imagegen_enabled
        structure_ready = bool((not prefs.structure_guides_enabled) or (not prefs.strict_composition_lock) or props.product_collection)
        needs_polish = generate_needs_polish(props, prefs)
        if props.two_step:
            go_text = "生成提示词" if needs_polish else "渲染"
        else:
            go_text = "生成"
        go = layout.row(align=True)
        go.scale_y = 1.6
        if props.status in {"POLISHING", "RENDERING"}:
            pct = max(0, min(100, int(round(float(props.progress) * 100))))
            stage = "写提示词" if props.status == "POLISHING" else "渲染"
            phase = getattr(props, "task_phase", "") or stage
            go.enabled = False
            text = f"{phase} · {pct}%"
            if hasattr(go, "progress"):
                go.progress(factor=max(0.0, min(1.0, float(props.progress))), text=text, type="BAR")
            else:
                go.prop(props, "progress", text=text, slider=True)
        else:
            go.enabled = bool(not busy and state == "LOGGED_IN" and camera and structure_ready and imagegen_enabled)
            go.operator("wondful.generate", text=go_text, icon="RENDER_STILL")
        if busy:
            cancel_row = layout.row(align=True)
            cancel_row.operator("wondful.cancel_task", text="取消", icon="CANCEL")
        else:
            next_step = (
                "先完成 ① 连接" if state != "LOGGED_IN" else
                "先在场景里设置活动相机" if not camera else
                "先选择产品集合" if not structure_ready else
                "ImageGen 已在偏好设置里关闭" if not imagegen_enabled else "")
            if next_step:
                layout.label(text=next_step, icon="INFO")
        if props.status == "ERROR" and props.last_error:
            err = layout.box()
            for line in wrap(props.last_error, width=42)[:6]:
                err.label(text=line, icon="ERROR")
            err.operator("wondful.copy_diagnostics", text="复制诊断信息", icon="COPYDOWN")

        # ---- 结果 ---------------------------------------------------------------
        provider_variant_count = render_variant_count("antigravity" if active_is_antigravity else "codex")
        if props.result_image:
            result_box = layout.box()
            title = result_box.row(align=True)
            title.label(text="结果", icon="IMAGE_DATA")
            if props.alignment_score >= 0:
                icon = "CHECKMARK" if props.alignment_score >= prefs.alignment_threshold else "ERROR"
                title.label(text=f"轮廓对齐 {props.alignment_score:.0f}", icon=icon)
            result_box.template_ID_preview(props, "result_image", rows=4, cols=7)
            actions = result_box.row(align=True)
            actions.scale_y = 1.2
            actions.operator("wondful.open_compare_workspace", text="对比", icon="ARROW_LEFTRIGHT")
            actions.operator("wondful.open_output_directory", text="打开文件夹", icon="FILE_FOLDER")
            again = actions.row(align=True)
            again.enabled = not busy
            again.operator("wondful.ai_render", text="再来一张", icon="FILE_REFRESH")
            exported_count = max(0, int(getattr(props, "variant_count", 0)))
            if props.status == "RENDERING" and props.last_export_path:
                result_box.label(text=f"已完成 {exported_count}/{provider_variant_count} 张，继续生成中", icon="TIME")
            elif exported_count > 1:
                result_box.label(text=f"共 {exported_count} 张，预览为最佳一张", icon="IMAGE_DATA")

        # ---- 高级 ---------------------------------------------------------------
        advanced = layout.box()
        if not _disclosure(advanced.row(align=True), props, "ui_show_advanced", "高级", icon="PREFERENCES"):
            return
        adv = advanced.column()

        ai = adv.box()
        ai.label(text="AI 与模型", icon="TOOL_SETTINGS")
        prov = ai.row(align=True)
        prov.enabled = not busy
        prov.prop(props, "analysis_provider", expand=True)
        model_provider = "antigravity" if active_is_antigravity else "codex"
        model_field = model_provider + "_model"
        models = getattr(props, model_provider + "_models")
        model_row = ai.row(align=True)
        model_row.enabled = not busy
        if models:
            try:
                model_row.prop_search(prefs, model_field, props, model_provider + "_models", text="推理模型", results_are_suggestions=True)
            except TypeError:
                model_row.prop_search(prefs, model_field, props, model_provider + "_models", text="推理模型")
        else:
            model_row.prop(prefs, model_field, text="推理模型")
        model_row.operator("wondful.refresh_models", text="", icon="FILE_REFRESH")
        model_row.operator("wondful.model_default", text="默认")
        msg = getattr(props, model_provider + "_models_message")
        if msg:
            ai.label(text=msg[:90])
        ai.label(text="生图：" + ("AGY generate_image" if active_is_antigravity else "Codex ImageGen") + "（由 CLI 管理）")
        acct = ai.row(align=True)
        acct.operator(refresh_op, text="检测登录", icon="FILE_REFRESH")
        if state == "LOGGED_IN" and not active_is_antigravity:
            acct.operator("wondful.codex_logout", text="退出登录", icon="X")
        if active_is_antigravity:
            acct.operator("wondful.antigravity_terminal", text="Google 登录", icon="CONSOLE")
        if cli_version:
            ai.label(text=cli_version[:90])
        if state == "LOGGED_IN" and account_message:
            ai.label(text=account_message[:90])

        flow = adv.box()
        flow.label(text="流程", icon="SETTINGS")
        flow.prop(props, "two_step", text="分两步：先写提示词，确认后再渲染")
        mode_row = flow.row(align=True)
        mode_row.label(text="模式")
        mode_row.prop(props, "render_mode", expand=True)
        out_row = flow.row(align=True)
        out_row.prop(props, "output_directory", text="输出")
        out_row.operator("wondful.choose_output_directory", text="", icon="FILEBROWSER")
        if not (props.output_directory or "").strip():
            flow.label(text="留空：保存过的工程输出到 .blend 旁边的 Wondful_Renders", icon="INFO")
        if camera:
            flow.label(text=f"相机：{camera.name} · {camera_w} × {camera_h}", icon="CAMERA_DATA")
        if not prefs.structure_guides_enabled:
            flow.label(text="结构控制图已在偏好设置中关闭", icon="ERROR")

        prompt_box = adv.box()
        if _disclosure(prompt_box.row(align=True), props, "ui_show_prompt", f"提示词 · {_prompt_char_count(props.prompt)} 字", icon="TEXT"):
            region_width = getattr(getattr(context, "region", None), "width", 330)
            ui_scale = getattr(getattr(context.preferences, "system", None), "ui_scale", 1.0)
            columns = max(16, int((region_width / max(.5, ui_scale) - 65) / 7.5))
            prompt_box.prop(props, "prompt_expanded", text="收起" if props.prompt_expanded else "展开全文", emboss=False)
            _draw_prompt_editor(prompt_box, props, columns)
            if props.prompt_notice:
                prompt_box.label(text=props.prompt_notice[:100], icon="INFO")
            if getattr(props, "prompt_removed_notice", ""):
                prompt_box.label(text=props.prompt_removed_notice[:100], icon="TRASH")
            polish = prompt_box.row(align=True)
            polish.enabled = bool(not busy and state == "LOGGED_IN")
            polish.operator("wondful.polish_prompt", text="只重写提示词", icon="TEXT")

        lock_box = adv.box()
        if _disclosure(lock_box.row(align=True), props, "ui_show_appearance_lock", "产品外观锁定（自动填写）", icon="LOCKED"):
            lock_box.prop(props, "color_source", text="配色来源")
            lock_box.prop(props, "product_look_prompt", text="产品外观")
            lock_box.prop(props, "identity_details", text="保留细节")
            fill = lock_box.row(align=True)
            fill.enabled = len(props.product_images) > 0 and not busy
            fill.operator("wondful.autofill_product_look", text="重新根据参考填写", icon="EYEDROPPER")
            if getattr(props, "product_autofill_message", ""):
                lock_box.label(text=props.product_autofill_message, icon="CHECKMARK")
            else:
                lock_box.label(text="留空即可，生成时会根据产品参考自动填写。", icon="INFO")
        if getattr(props, "style_summary_cache", "") and len(props.style_images) > 0:
            summary_box = adv.box()
            if _disclosure(summary_box.row(align=True), props, "ui_show_style_summary", "环境分析（可编辑）", icon="LIGHT_SUN"):
                summary_box.prop(props, "style_summary_cache", text="")

        more_refs = adv.box()
        _draw_reference_group(more_refs, props, "人物参考", "person_images", "person_image_index", "PERSON", "ui_show_person_refs")
        total = len(props.product_images) + len(props.person_images) + len(props.style_images)
        if total > 0 and not busy:
            more_refs.operator("wondful.auto_classify_references", text="Jev 语义整理参考图", icon="LIGHT")
        if getattr(props, "jev_status_message", ""):
            more_refs.label(text=props.jev_status_message[:100], icon="INFO")

        if props.result_image:
            info = adv.box()
            info.label(text="上次渲染", icon="INFO")
            if props.last_export_path:
                info.label(text=f"输出：{props.last_export_path[:100]}")
            if props.alignment_attempts:
                info.label(text=f"尝试 {props.alignment_attempts} 次 · Session {props.last_session_id}")
            if props.last_canvas_warning:
                for line in wrap(props.last_canvas_warning, width=44)[:3]:
                    info.label(text=line)
            if props.last_structure_note:
                info.label(text=props.last_structure_note[:100])
            if props.last_total_seconds > 0:
                info.label(text=f"总用时 {props.last_total_seconds:.0f}s · 生图 {props.last_generation_seconds:.0f}s · 验收 {props.last_audit_seconds:.0f}s")
            if getattr(props, "active_conversation_id", ""):
                info.operator("wondful.copy_conversation_id", text="复制远程会话恢复命令", icon="COPYDOWN")

        tools = adv.row(align=True)
        tools.operator("wondful.copy_diagnostics", text="复制诊断信息", icon="COPYDOWN")
        tools.operator("preferences.addon_show", text="插件偏好设置").module = __package__
