"""Bound image-tool inputs without dropping references or changing Camera Base."""
import math
import re
from pathlib import Path

MAX_IMAGE_PATHS = 5  # Codex image tool limit
MAX_ANTIGRAVITY_IMAGE_PATHS = 3  # AGY generate_image limit


class ReferenceLimitError(RuntimeError):
    pass


def unique_paths(paths):
    return list(dict.fromkeys(str(Path(p).expanduser().resolve()) for p in paths if p))


def check_image_capacity(paths, limit=MAX_IMAGE_PATHS):
    count = len(unique_paths(paths))
    if count > limit:
        raise ReferenceLimitError(f"本轮图像输入 {count} 张，超过当前提交上限 {limit} 张。请由插件重新整理参考图集后提交；这不是登录失效。")


def reference_limit_error(text):
    return bool(re.search(r"最多支持\s*\d+\s*个?\s*参考图|参考图[^\n]{0,30}(?:超限|超过)|"
                          r"(?:maximum|max|at most|up to)[^\n]{0,45}\b\d+\b[^\n]{0,45}(?:images?|image paths|reference)|"
                          r"too many (?:input |reference )?images", text or "", re.I))


def bundle_plan(groups, reserve=0, limit=MAX_IMAGE_PATHS):
    """groups=[(role, paths)]; first role must be camera. Keep every logical input."""
    if not groups or groups[0][0] != "camera" or len(groups[0][1]) != 1:
        raise ValueError("One authoritative camera image is required")
    slots = limit - reserve
    if slots < 2:
        raise ValueError("Not enough slots for camera plus bundled references")
    numbered, index = [], 1
    for group in groups:
        if len(group) == 2:
            role, paths = group
            sub_roles = []
        elif len(group) == 3:
            role, paths, sub_roles = group
        else:
            raise ValueError("Each reference group must be (role, paths) or (role, paths, sub_roles)")
        members = []
        for member_index, path in enumerate(paths):
            sub_role = str(sub_roles[member_index]) if member_index < len(sub_roles) else ""
            members.append({"reference": index, "role": role, "sub_role": sub_role, "path": str(path)})
            index += 1
        if members:
            numbered.append({"role": role, "members": members})
    if index - 1 <= slots:
        return [{"role": g["role"], "members": [m]} for g in numbered for m in g["members"]]
    # Each semantic class gets its own sheet. Only merge appearance classes when
    # repair inputs consume two slots; roles remain explicitly labelled per cell.
    if len(numbered) > slots:
        fixed = [g for g in numbered if g["role"] in {"camera", "structure"}]
        appearance = [m for g in numbered if g["role"] not in {"camera", "structure"} for m in g["members"]]
        numbered = fixed + ([{"role": "appearance", "members": appearance}] if appearance else [])
    if len(numbered) > slots and slots == 2:
        camera_group = next((g for g in numbered if g["role"] == "camera"), None)
        if camera_group is None:
            raise ReferenceLimitError("缺少 Camera Base。")
        merged_members = [m for g in numbered if g is not camera_group for m in g["members"]]
        numbered = [camera_group] + ([{"role": "control_bundle", "members": merged_members}] if merged_members else [])
    if len(numbered) > slots:
        raise ReferenceLimitError("参考图无法在当前容量中完整编排。")
    return numbered


_DIGITS = {
    'R': ('11110','10001','11110','10100','10010','10001','10001'),
    '0': ('01110','10001','10011','10101','11001','10001','01110'),
    '1': ('00100','01100','00100','00100','00100','00100','01110'),
    '2': ('01110','10001','00001','00010','00100','01000','11111'),
    '3': ('11110','00001','00001','01110','00001','00001','11110'),
    '4': ('00010','00110','01010','10010','11111','00010','00010'),
    '5': ('11111','10000','11110','00001','00001','10001','01110'),
    '6': ('00110','01000','10000','11110','10001','10001','01110'),
    '7': ('11111','00001','00010','00100','01000','01000','01000'),
    '8': ('01110','10001','10001','01110','10001','10001','01110'),
    '9': ('01110','10001','10001','01111','00001','00010','01100'),
}


def compose_sheet(members, read_rgba):
    """Pure array layout. Each original keeps its aspect; labels live outside it."""
    import numpy as np
    from .compare_core import resize_rgba_nearest
    cols = max(1, int(math.ceil(math.sqrt(len(members)))))
    rows = int(math.ceil(len(members) / cols))
    tile_w = min(1152, 4096 // cols)
    tile_h, bar = int(tile_w * .72), 40
    sheet = np.full((rows * (tile_h + bar), cols * tile_w, 4), .12, dtype=np.float32)
    sheet[:, :, 3] = 1
    for i, member in enumerate(members):
        rgba = read_rgba(member['path'])
        h, w = rgba.shape[:2]
        scale = min((tile_w-16)/w, (tile_h-16)/h)
        tw, th = max(1,int(w*scale)), max(1,int(h*scale))
        image = resize_rgba_nearest(rgba, tw, th)
        row, col = divmod(i,cols)
        x, y = col*tile_w + (tile_w-tw)//2, row*(tile_h+bar) + bar + (tile_h-th)//2
        sheet[y:y+th,x:x+tw] = image
        for j,char in enumerate('R'+str(member['reference'])):
            for gy,line in enumerate(_DIGITS[char]):
                for gx,bit in enumerate(line):
                    if bit == '1':
                        left,top=col*tile_w+12+j*24+gx*3,row*(tile_h+bar)+8+gy*3
                        sheet[top:top+3,left:left+3,:3]=1
    return sheet


def write_sheet(path, members):
    """Main-thread Blender image I/O; never invoked from a generation worker."""
    import bpy
    import numpy as np
    from .structure_control import _save_rgba
    def read_rgba(source):
        image = bpy.data.images.load(str(source), check_existing=False)
        try:
            # Read encoded reference colors, avoiding scene view transforms.
            image.colorspace_settings.name = 'Non-Color'
            w,h = map(int,image.size)
            pixels=np.empty(w*h*4,dtype=np.float32)
            image.pixels.foreach_get(pixels)
            return pixels.reshape(h,w,4)[::-1].copy()
        finally:
            bpy.data.images.remove(image)
    _save_rgba(Path(path), compose_sheet(members,read_rgba), 'Wondful_ReferenceSheet')
    return str(path)


def prepare_bundle(groups, directory, reserve=0, writer=write_sheet, limit=MAX_IMAGE_PATHS):
    limit = max(1, int(limit))
    reserve = max(0, int(reserve))
    plan = bundle_plan(groups, reserve=reserve, limit=limit)
    paths, lines, manifest = [], [], []
    for i, group in enumerate(plan,1):
        members = group['members']
        if len(members) == 1:
            path = members[0]['path']
        else:
            path = writer(Path(directory)/f'reference_sheet_{i:02d}_{group["role"]}.png',members)
        paths.append(str(path))
        mapping = ', '.join(
            f'R{m["reference"]} = {m["role"]}' + (f'/{m.get("sub_role")}' if m.get("sub_role") else '')
            for m in members
        )
        lines.append(f'输入路径 {i}: {path}\n  格内标签：{mapping}。按从左到右、从上到下排列。')
        manifest.append({'path':str(path),'members':members})
    check_image_capacity(paths, limit - reserve)
    note = ('\n\n【图像工具输入清单：本轮优先使用此路径表】\n'
            '本任务中的 Reference N / R N 是逻辑参考编号；若在图集中，它指格内标签，不是工具路径下标。'
            '白模 Camera 始终独立、完整、无缩放拼贴。图集仅供逐格读取，不得生成拼贴或复制标签。'
            '结构格只管几何；产品格只管造型；环境格决定产品打光。'
            '调用生图工具时，只使用以下路径及本轮明确给出的编辑底图/Mask，不要重新追加图集内的原始路径。\n'
            + '\n'.join(lines))
    return paths, note, {'limit':limit,'reserved_repair_inputs':reserve,'input_count':len(paths),'groups':manifest}
