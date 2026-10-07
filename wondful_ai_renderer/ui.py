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
    meta.label(text=primary_text if index == 0 else f"辅助 {index + 1}", icon=icon0 if index == 0 else "IMAGE_DATA")
    if item.image:
        name = item.image.name
        meta.label(text=name if len(name) <= 24 else name[:21] + "…")
    meta.prop(item, "instruction", text="造型重点" if kind == "PRODUCT" else "参考什么")
    controls = meta.row(align=True)
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
    add_text = "换图" if kind == "STYLE" and collection else "文件"
    add_icon = "FILE_REFRESH" if kind == "STYLE" and collection else "ADD"
    add = header.operator("wondful.load_reference", text=add_text, icon=add_icon)
    add.ref_kind = kind
    paste = header.operator("wondful.paste_reference", text=("替换粘贴" if kind == "STYLE" and collection else "粘贴"))
    paste.ref_kind = kind
    if collection:
        clear_all = header.operator("wondful.clear_all_references", text="", icon="TRASH")
        clear_all.ref_kind = kind
    if not opened:
        return

    if kind == "PRODUCT":
        box.label(text="仅参考产品造型，不参考原图打光。", icon="INFO")
    elif kind == "STYLE":
        box.label(text="决定产品受光、反射、阴影与环境氛围。", icon="LIGHT")
    if not collection:
        empty = box.column(align=True)
        empty.label(text="拖入文件，或复制图片后点“粘贴”", icon="IMAGE_DATA")
        empty.label(text=("第一张决定主光，可用箭头调整顺序；每类最多 8 张。" if kind == "STYLE" else "第一张自动作为主参考；每类最多 8 张。"))
        return

    # The preview and its identity/controls now live in one card. There is no
    # detached name list + selected-image preview anymore.
    for index, item in enumerate(collection):
        _draw_reference_card(box, props, item, index, kind)


class WONDFUL_PT_main(Panel):
    bl_label = "Wondful AI 渲染器 · 3.1.4"
    bl_idname = "WONDFUL_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wondful AI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.wondful_ai
        prefs = _prefs(context)
        busy = props.status in {"AUTHENTICATING", "CLASSIFYING", "POLISHING", "RENDERING", "REFRESHING_MODELS"}

        # ---- Provider / camera -------------------------------------------------
        top = layout.box()
        provider_row = top.row(align=True)
        provider_row.label(text="AI Provider", icon="TOOL_SETTINGS")
        provider_row.enabled = not busy
        provider_row.prop(props, "analysis_provider", expand=True)

        active_is_antigravity = props.analysis_provider == "ANTIGRAVITY"
        model_provider = "antigravity" if active_is_antigravity else "codex"
        model_field = model_provider + "_model"
        models = getattr(props, model_provider + "_models")
        model_row = top.row(align=True)
        model_row.enabled = not busy
        if models:
            try:
                model_row.prop_search(prefs, model_field, props, model_provider + "_models", text="推理模型", results_are_suggestions=True)
            except TypeError:
                model_row.prop_search(prefs, model_field, props, model_provider + "_models", text="推理模型")
        else:
            model_row.prop(prefs, model_field, text="推理模型")
        model_row.operator("wondful.refresh_models", text="刷新", icon="FILE_REFRESH")
        model_row.operator("wondful.model_default", text="默认")
        selected_model = getattr(prefs, model_field).strip()
        top.label(text="当前选择：" + (selected_model or "CLI 默认"))
        selected = next((item for item in models if item.name == selected_model), None)
        if selected and selected.label != selected.name:
            top.label(text=selected.label)
        for line in wrap(getattr(props, model_provider + "_models_message"), width=34):
            top.label(text=line)
        top.label(text="生图引擎：" + ("AGY generate_image" if active_is_antigravity else "Codex ImageGen"))
        top.label(text="生图模型由内置工具管理，不能在此切换")
        state = props.antigravity_account_state if active_is_antigravity else props.codex_account_state
        account_message = props.antigravity_account_message if active_is_antigravity else props.codex_account_message
        cli_version = props.antigravity_cli_version if active_is_antigravity else props.codex_cli_version
        provider_label = "Antigravity" if active_is_antigravity else "Codex"
        refresh_op = "wondful.antigravity_check" if active_is_antigravity else "wondful.codex_check"

        task_text = {
            "IDLE": "就绪",
            "AUTHENTICATING": "登录中",
            "POLISHING": "润色中",
            "RENDERING": "渲染中",
            "REFRESHING_MODELS": "读取模型中",
            "CLASSIFYING": "参考图分类中",
            "SUCCESS": "完成",
            "ERROR": "任务错误",
        }.get(props.status, props.status)

        # Logged-in account management is intentionally hidden from the main flow.
        # If the active provider is not logged in, keep the existing prominent state
        # and login controls so the user can recover immediately.
        if state != "LOGGED_IN":
            row = top.row(align=True)
            account_icons = {
                "UNKNOWN": "QUESTION",
                "NOT_INSTALLED": "ERROR",
                "LOGGED_OUT": "ERROR",
                "ERROR": "ERROR",
            }
            account_text = {
                "UNKNOWN": f"{provider_label} 未检测",
                "NOT_INSTALLED": f"{provider_label} CLI 未安装",
                "LOGGED_OUT": ("Google 未登录" if active_is_antigravity else "ChatGPT 未登录"),
                "ERROR": f"{provider_label} 异常",
            }.get(state, state)
            if active_is_antigravity and props.status == "AUTHENTICATING":
                account_text = "正在连接 Google"
            elif active_is_antigravity and state == "UNKNOWN" and props.antigravity_cli_resolved:
                account_text = "AGY 待连接验证"
            row.label(text=account_text, icon=account_icons.get(state, "INFO"))
            row.operator(refresh_op, text="", icon="FILE_REFRESH")
            row.label(text=task_text, icon="TIME" if busy else ("ERROR" if props.status == "ERROR" else "CHECKMARK"))

            if active_is_antigravity:
                connect = top.row(align=True)
                connect.enabled = not busy
                connect.operator("wondful.antigravity_terminal", text="Google 登录", icon="USER")
                connect.operator("wondful.antigravity_login", text="验证登录", icon="CHECKMARK")
                top.label(text="终端与浏览器完成登录后，回来点验证登录")
            else:
                connect = top.row(align=True)
                connect.enabled = not busy
                connect.operator("wondful.codex_login", text="使用 ChatGPT 登录", icon="USER")
            details = top.row(align=True)
            if _disclosure(details, props, "ui_show_account", "账号详情"):
                account = top.column(align=True)
                if cli_version:
                    account.label(text=cli_version)
                if account_message:
                    account.label(text=account_message[:110])
                controls = account.row(align=True)
                if active_is_antigravity:
                    controls.operator("wondful.antigravity_check", text="检测安装", icon="FILE_REFRESH")
                    bridge = controls.operator("wondful.antigravity_login", text="插件内授权（兼容）", icon="CONSOLE")
                    bridge.allow_interactive = True
                    account.label(text="Antigravity 登录由 agy + 系统 Keychain 管理；插件不读取 OAuth Token。", icon="INFO")
                else:
                    controls.operator("wondful.codex_login", text="使用 ChatGPT 登录", icon="USER")
                    controls.operator("wondful.codex_check", text="检测", icon="FILE_REFRESH")
        elif props.status == "ERROR":
            # Logged-in account state stays hidden. Task progress belongs to the
            # action button itself; only errors are surfaced at the top.
            task = top.row(align=True)
            task.label(text=task_text, icon="ERROR")

        camera = context.scene.camera
        camera_w, camera_h = camera_output_dimensions(context)

        # Task progress is shown directly in the AI 润色 / AI 渲染 action slot.
        # Keep authentication status here because it has no workflow action button.
        if props.status == "AUTHENTICATING":
            if active_is_antigravity:
                auth = top.box()
                for line in wrap(props.auth_detail or "正在连接 AGY", width=38):
                    auth.label(text=line)
                if props.auth_has_url:
                    auth.operator("wondful.antigravity_auth_browser", text="打开本次登录页", icon="URL")
                if props.auth_stage == "WAITING_CODE":
                    auth.prop(context.window_manager, "wondful_auth_code", text="授权码")
                    auth.operator("wondful.antigravity_submit_code", text="提交授权码", icon="CHECKMARK")
                auth.operator("wondful.antigravity_auth_cancel", text="取消连接", icon="CANCEL")
            else:
                top.prop(props, "progress", text="等待授权", slider=True)
        if props.status == "ERROR" and props.last_error:
            err = top.box()
            for line in wrap(props.last_error, width=42):
                err.label(text=line, icon="ERROR")
            err.operator("wondful.copy_diagnostics", text="复制诊断信息", icon="COPYDOWN")

        # ---- Prompt ------------------------------------------------------------
        prompt_box = layout.box()
        prompt_header = prompt_box.row(align=True)
        prompt_header.label(text=f"提示词 · {_prompt_char_count(props.prompt)} 字", icon="TEXT")
        prompt_header.prop(props, "prompt_expanded", text="收起" if props.prompt_expanded else "展开全文",
                           icon="TRIA_UP" if props.prompt_expanded else "TRIA_DOWN", emboss=False)
        region_width = getattr(getattr(context, "region", None), "width", 330)
        ui_scale = getattr(getattr(context.preferences, "system", None), "ui_scale", 1.0)
        columns = max(16, int((region_width / max(.5, ui_scale) - 65) / 7.5))
        _draw_prompt_editor(prompt_box, props, columns)
        if props.prompt_notice:
            prompt_box.label(text=props.prompt_notice, icon="INFO")
        if getattr(props, "prompt_removed_notice", ""):
            prompt_box.label(text=props.prompt_removed_notice[:110], icon="TRASH")

        policy_stale = needs_reference_policy_refresh(props)
        target_stale = prompt_profiles.needs_target_refresh(props, prefs)
        style_stale = bool(
            policy_stale
            or props.style_prompt_dirty
            or int(props.prompt_style_revision) != int(props.style_reference_revision)
            or (len(props.style_images) > 0 and not bool(props.style_sync_initialized))
        )

        # ---- References: configure what each image should contribute ----------
        refs = layout.box()
        total = len(props.product_images) + len(props.person_images) + len(props.style_images)
        header = refs.row(align=True)
        opened = _disclosure(header, props, "ui_show_references", "参考图", icon="IMAGE_DATA", suffix=f"  {total}")
        if opened:
            if total > 0 and not busy:
                action_row = refs.row(align=True)
                action_row.operator("wondful.auto_classify_references", text="Jev 语义整理", icon="LIGHT")
            if getattr(props, "jev_status_message", ""):
                refs.label(text=props.jev_status_message[:110], icon="INFO")
            _draw_reference_group(refs, props, "产品造型", "product_images", "product_image_index", "PRODUCT", "ui_show_product_refs")
            _draw_reference_group(refs, props, "人物", "person_images", "person_image_index", "PERSON", "ui_show_person_refs")
            _draw_reference_group(refs, props, "环境／风格", "style_images", "style_image_index", "STYLE", "ui_show_style_refs")

        # 3.1.7: product appearance lock sits between references and polish.
        lock_box = layout.box()
        if _disclosure(lock_box.row(align=True), props, "ui_show_appearance_lock", "产品外观锁定", icon="LOCKED"):
            lock_box.prop(props, "color_source", text="配色来源")
            lock_box.prop(props, "product_look_prompt", text="产品外观")
            lock_box.prop(props, "identity_details", text="保留细节")
            hint = lock_box.column(align=True)
            hint.scale_y = 0.8
            hint.label(text="外观锁定原样进入生图指令；换环境只重写环境与光影。", icon="INFO")
            if getattr(props, "jev_identity_assets", ""):
                hint.label(text=("Jev 识别：" + props.jev_identity_assets)[:90], icon="LIGHT")
        if getattr(props, "style_summary_cache", "") and len(props.style_images) > 0:
            summary_box = layout.box()
            if _disclosure(summary_box.row(align=True), props, "ui_show_style_summary", "环境分析（可编辑）", icon="LIGHT_SUN"):
                summary_box.prop(props, "style_summary_cache", text="")
                summary_box.label(text="修改后再点 AI 润色，会按修改后的分析重写提示词。", icon="INFO")

        # AI prompt generation comes after reference configuration in the workflow.
        polish = layout.row(align=True)
        polish.scale_y = 1.25
        if policy_stale:
            refs.label(text="参考职责已更新，请重新生成提示词。", icon="INFO")
        polish_text = ("适配当前引擎" if target_stale else
                       "重新生成提示词" if style_stale else "AI 润色")
        polish_label = f"{polish_text} · {'Antigravity' if props.analysis_provider == 'ANTIGRAVITY' else 'Codex'}"
        _draw_progress_action(
            polish,
            props,
            active_status="POLISHING",
            idle_text=polish_label,
            icon="FILE_REFRESH" if style_stale else "TEXT",
            operator="wondful.polish_prompt",
            enabled=bool(not busy and state == "LOGGED_IN"),
        )

        if busy:
            cancel_row = layout.row(align=True)
            cancel_row.scale_y = 1.2
            cancel_row.operator("wondful.cancel_task", text="取消当前任务", icon="CANCEL")

        # ---- Render: follows references in actual operation order --------------
        render_box = layout.box()
        render_box.label(text="AI 渲染", icon="RENDER_STILL")

        mode_row = render_box.row(align=True)
        mode_row.label(text="模式", icon="SETTINGS")
        mode_row.prop(props, "render_mode", expand=True)
        structure = render_box.column(align=True)
        structure.label(text="Blender Structure Lock", icon="MOD_WIREFRAME")
        if camera:
            structure.label(text=f"结构参考相机：{camera.name} · {camera_w} × {camera_h}", icon="CAMERA_DATA")
        else:
            structure.label(text="当前 Scene 未设置活动相机", icon="ERROR")

        collection_row = structure.row(align=True)
        collection_row.prop(props, "product_collection", text="产品集合")
        if props.product_collection:
            mesh_count = sum(1 for obj in props.product_collection.all_objects if getattr(obj, "type", "") == "MESH")
            structure.label(text=f"集合内 Mesh：{mesh_count} · 集合及子集合全部视为产品", icon="OUTLINER_COLLECTION")

        else:
            structure.label(text="请选择产品集合；不会再自动使用全场景 Mesh。", icon="ERROR")
        if not prefs.structure_guides_enabled:
            structure.label(text="Structure Packet 已在插件偏好设置中关闭", icon="ERROR")

        # ---- Output ------------------------------------------------------------
        output = render_box.column(align=True)
        output.label(text="渲染输出", icon="FILE_FOLDER")
        path_row = output.row(align=True)
        path_row.prop(props, "output_directory", text="")
        path_row.operator("wondful.choose_output_directory", text="选择", icon="FILEBROWSER")
        path_row.operator("wondful.open_output_directory", text="", icon="FILE_FOLDER")
        if not (props.output_directory or "").strip():
            if (prefs.output_directory or "").strip():
                output.label(text="当前工程未单独指定，将使用插件全局输出目录。", icon="INFO")
            else:
                output.label(text="留空：已保存工程用 //Wondful_Renders；未保存工程用 Pictures/Wondful_AI_Renderer", icon="INFO")

        render_row = render_box.row(align=True)
        render_row.scale_y = 1.45
        provider_imagegen_enabled = prefs.codex_imagegen_enabled if props.analysis_provider == "CODEX" else prefs.antigravity_imagegen_enabled
        render_label = "Antigravity" if props.analysis_provider == "ANTIGRAVITY" else "Codex"
        provider_variant_count = render_variant_count("antigravity" if props.analysis_provider == "ANTIGRAVITY" else "codex")
        structure_ready = bool(
            (not prefs.structure_guides_enabled)
            or (not prefs.strict_composition_lock)
            or props.product_collection
        )
        _draw_progress_action(
            render_row,
            props,
            active_status="RENDERING",
            idle_text=f"AI 渲染 · {render_label} ×{provider_variant_count}",
            icon="RENDER_STILL",
            operator="wondful.ai_render",
            enabled=bool(provider_imagegen_enabled and not style_stale and not target_stale and not busy and structure_ready and camera and props.prompt.strip() and state == "LOGGED_IN"),
        )

        if not busy:
            next_step = (
                "请先连接并验证账号" if state != "LOGGED_IN" else
                "请先适配当前引擎的提示词" if target_stale else
                "参考图已更新，请先重新生成提示词" if style_stale else
                "请输入或生成提示词" if not props.prompt.strip() else
                "请设置 Scene 活动相机" if not camera else
                "请选择产品集合" if not structure_ready else "")
            if next_step:
                render_box.label(text=next_step, icon="INFO")

        # ---- Result ------------------------------------------------------------
        if props.result_image:
            result_box = layout.box()
            title = result_box.row(align=True)
            title.label(text="最新渲染", icon="IMAGE_DATA")
            if props.alignment_score >= 0:
                icon = "CHECKMARK" if props.alignment_score >= prefs.alignment_threshold else "ERROR"
                title.label(text=f"对齐 {props.alignment_score:.0f}", icon=icon)
            result_box.template_ID_preview(props, "result_image", rows=4, cols=7)
            actions2 = result_box.row(align=True)
            actions2.scale_y = 1.25
            actions2.operator("wondful.open_compare_workspace", text="打开渲染对比", icon="ARROW_LEFTRIGHT")
            actions2.operator("wondful.open_output_directory", text="打开输出目录", icon="FILE_FOLDER")
            if props.last_export_path:
                result_box.label(text=f"输出：{props.last_export_path[:110]}", icon="CHECKMARK")
                exported_count = max(0, int(getattr(props, "variant_count", 0)))
                if props.status == "RENDERING":
                    result_box.label(text=f"已完成并导出 {exported_count}/{provider_variant_count} 张；继续生成中", icon="TIME")
                elif props.status == "ERROR" and exported_count < provider_variant_count:
                    result_box.label(text=f"已完成并导出 {exported_count}/{provider_variant_count} 张；其余结果未生成", icon="INFO")
            if getattr(props, "variant_count", 1) > 1:
                result_box.label(text=f"本次已导出 {props.variant_count} 张独立结果；上方预览为最佳图", icon="IMAGE_DATA")
            if props.alignment_attempts:
                result_box.label(text=f"生成尝试 {props.alignment_attempts} 次 · Session {props.last_session_id}", icon="INFO")
            if getattr(props, "jev_identity_assets", ""):
                result_box.label(text=f"身份关键资产：{props.jev_identity_assets[:100]}", icon="LOCKED")
            if getattr(props, "jev_status", ""):
                result_box.label(text=f"语义层：{props.jev_status}", icon="LIGHT")
            if getattr(props, "active_conversation_id", ""):
                conv_row = result_box.row(align=True)
                conv_row.label(text=f"远程会话：{props.active_conversation_id[:18]}...", icon="WORLD")
                conv_row.operator("wondful.copy_conversation_id", text="复制恢复命令", icon="COPYDOWN")
            if props.last_canvas_warning:
                for line in wrap(props.last_canvas_warning, width=44):
                    result_box.label(text=line, icon="INFO" if getattr(props, "last_canvas_fit", False) else "ERROR")
            if props.last_structure_note:
                result_box.label(text=props.last_structure_note, icon="INFO")
            if props.last_total_seconds > 0:
                result_box.label(text=f"总用时 {props.last_total_seconds:.0f}s · 本地准备 {props.last_preparation_seconds:.0f}s", icon="TIME")
            if props.last_generation_seconds > 0:
                timing_text = f"生图 {props.last_generation_seconds:.0f}s" if props.last_generation_seconds < 60 else f"生图 {props.last_generation_seconds/60.0:.1f} 分钟"
                if props.last_audit_seconds > 0:
                    timing_text += f" · 验收 {props.last_audit_seconds:.0f}s" if props.last_audit_seconds < 60 else f" · 验收 {props.last_audit_seconds/60.0:.1f} 分钟"
                result_box.label(text=timing_text, icon="TIME")

        # ---- Advanced / settings ----------------------------------------------
        advanced = layout.box()
        row = advanced.row(align=True)
        opened = _disclosure(row, props, "ui_show_advanced", "高级设置", icon="PREFERENCES")
        if opened:
            from . import jev_semantics
            jev = jev_semantics.backend_status()
            jev_box = advanced.box()
            jev_box.label(text="TypeSafe / Jev 语义层", icon="LIGHT")
            jev_box.label(text=jev.get("message", "Jev 状态未知")[:110])
            if not jev.get("configured"):
                jev_box.label(text="设置环境变量 TYPESAFE_API_KEY 后启用真实 Jev；未配置时自动使用本地规则。", icon="INFO")
            else:
                jev_box.label(text="Jev 仅负责语义判断；构图/几何仍由 Blender，最终视觉仍由当前生图 Provider 负责。", icon="INFO")
            # When already logged in, account management lives here instead of
            # consuming space in the primary workflow.
            if state == "LOGGED_IN":
                account = advanced.box()
                account.label(text=f"账号 · {provider_label} 已登录", icon="CHECKMARK")
                if cli_version:
                    account.label(text=cli_version)
                if account_message:
                    account.label(text=account_message[:110])
                controls = account.row(align=True)
                controls.operator(refresh_op, text="检测安装" if active_is_antigravity else "检测登录状态", icon="FILE_REFRESH")
                if active_is_antigravity:
                    controls.operator("wondful.antigravity_login", text="连接验证", icon="USER")
                    controls.operator("wondful.antigravity_terminal", text="Google 登录", icon="CONSOLE")
                    account.label(text="Google OAuth 由 agy + 系统 Keychain 管理；插件不保存 Token。", icon="INFO")
                else:
                    controls.operator("wondful.codex_logout", text="退出登录", icon="X")
                    account.label(text="ChatGPT OAuth 由官方 Codex CLI 管理；插件不保存 Token。", icon="INFO")

            ratio = camera_w / camera_h if camera_h else 1.0
            if props.analysis_provider == "ANTIGRAVITY":
                advanced.label(text=f"分析模型：{prefs.antigravity_model or 'Antigravity 当前默认'}")
            else:
                advanced.label(text=f"分析模型：{prefs.codex_model or 'Codex 当前默认'}")
            render_engine = "Antigravity generate_image" if props.analysis_provider == "ANTIGRAVITY" else "Codex ImageGen"
            advanced.label(text=f"渲染引擎：{render_engine}")
            advanced.label(text="生图模型由 CLI 工具决定，与推理模型不同")
            advanced.label(text="Prompt Director 1.0 · " + ("Gemini 叙述适配" if active_is_antigravity else "OpenAI 编辑规格适配"))
            if active_is_antigravity and props.agy_image_capability == "NOT_LISTED":
                advanced.label(text="连接成功，但当前会话未列出 generate_image", icon="ERROR")
            advanced.operator("wondful.copy_diagnostics", text="复制诊断信息", icon="COPYDOWN")
            advanced.label(text=f"目标长边：{prefs.long_edge}px · 比例 {ratio:.3f}:1")
            advanced.label(text=f"构图锁定：{'严格' if prefs.strict_composition_lock else '普通'}")
            advanced.label(text=f"结构控制图：{'开启' if prefs.structure_guides_enabled else '关闭'} · 局部结构修复：{'开启' if prefs.masked_alignment_repair else '关闭'}")
            if props.render_mode == "STRICT" and prefs.auto_alignment_retry:
                advanced.label(text=f"当前严格模式：自动校验 {prefs.alignment_threshold}/100 · 最多 {prefs.alignment_max_attempts} 次")
            elif props.render_mode == "STRICT":
                advanced.label(text="当前严格模式：自动构图校验已在偏好设置关闭")
            else:
                advanced.label(text="当前快速链路：渲染后不调用远程构图验收")
            imagegen_enabled = prefs.antigravity_imagegen_enabled if props.analysis_provider == "ANTIGRAVITY" else prefs.codex_imagegen_enabled
            advanced.label(text=f"ImageGen：{'启用' if imagegen_enabled else '关闭'}")

            def _timeout_text(value):
                return "不限" if int(value) <= 0 else f"{int(value)}s"

            if props.analysis_provider == "ANTIGRAVITY":
                advanced.label(text=f"Antigravity 超时：润色 {_timeout_text(prefs.antigravity_polish_timeout)} · 验收 {_timeout_text(prefs.antigravity_audit_timeout)} · 渲染 {_timeout_text(prefs.antigravity_render_timeout)}")
            else:
                advanced.label(text=f"Codex 超时：润色 {_timeout_text(prefs.codex_polish_timeout)} · 验收 {_timeout_text(prefs.codex_audit_timeout)} · 渲染 {_timeout_text(prefs.codex_render_timeout)}")
            advanced.operator("preferences.addon_show", text="插件偏好设置").module = __package__
