from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


class ClipboardImageError(RuntimeError):
    pass


def _run(cmd: list[str], *, timeout: int = 20, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def _save_macos(destination: Path) -> None:
    def apple_script(kind: str, out_path: Path) -> tuple[int, str]:
        safe = str(out_path).replace('\\', '\\\\').replace('"', '\\"')
        script = (
            f'set outFile to POSIX file "{safe}"\n'
            'try\n'
            f'  set imageData to the clipboard as «class {kind}»\n'
            'on error errMsg\n'
            '  return "NO_IMAGE:" & errMsg\n'
            'end try\n'
            'set fileRef to open for access outFile with write permission\n'
            'try\n'
            '  set eof fileRef to 0\n'
            '  write imageData to fileRef\n'
            '  close access fileRef\n'
            'on error errMsg\n'
            '  try\n'
            '    close access fileRef\n'
            '  end try\n'
            '  return "WRITE_ERROR:" & errMsg\n'
            'end try\n'
            'return "OK"\n'
        )
        proc = _run(['osascript', '-e', script])
        text = (proc.stdout or b'').decode('utf-8', 'replace').strip()
        return proc.returncode, text

    code, text = apple_script('PNGf', destination)
    if code == 0 and text == 'OK' and destination.exists() and destination.stat().st_size > 0:
        return

    # Finder copy often exposes a file alias rather than pixel clipboard data.
    alias_proc = _run(['osascript', '-e', 'try\nset f to the clipboard as alias\nreturn POSIX path of f\non error\nreturn ""\nend try'])
    alias_path = (alias_proc.stdout or b'').decode('utf-8', 'replace').strip()
    if alias_path:
        src = Path(alias_path).expanduser()
        if src.is_file() and src.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'}:
            if src.suffix.lower() == '.png':
                shutil.copy2(src, destination)
            else:
                sips = shutil.which('sips') or '/usr/bin/sips'
                proc = _run([sips, '-s', 'format', 'png', str(src), '--out', str(destination)])
                if proc.returncode != 0:
                    try:
                        destination.unlink(missing_ok=True)
                    except Exception:
                        pass
            if destination.exists() and destination.stat().st_size > 0:
                return

    tiff = destination.with_suffix('.tiff')
    code, text = apple_script('TIFF', tiff)
    if code == 0 and text == 'OK' and tiff.exists() and tiff.stat().st_size > 0:
        sips = shutil.which('sips') or '/usr/bin/sips'
        proc = _run([sips, '-s', 'format', 'png', str(tiff), '--out', str(destination)])
        try:
            tiff.unlink(missing_ok=True)
        except Exception:
            pass
        if proc.returncode == 0 and destination.exists() and destination.stat().st_size > 0:
            return
    raise ClipboardImageError('剪贴板中没有可读取的 PNG/TIFF 图片。请先复制图片或截图，再点击“粘贴”。')


def _save_windows(destination: Path) -> None:
    ps = shutil.which('powershell') or shutil.which('pwsh')
    if not ps:
        raise ClipboardImageError('未找到 PowerShell，无法读取 Windows 图片剪贴板。')
    safe = str(destination).replace("'", "''")
    script = (
        'Add-Type -AssemblyName System.Windows.Forms; '
        'Add-Type -AssemblyName System.Drawing; '
        '$img=[System.Windows.Forms.Clipboard]::GetImage(); '
        'if ($null -eq $img) { exit 7 }; '
        f"$img.Save('{safe}', [System.Drawing.Imaging.ImageFormat]::Png);"
    )
    proc = _run([ps, '-NoProfile', '-NonInteractive', '-Command', script])
    if proc.returncode != 0 or not destination.exists() or destination.stat().st_size == 0:
        raise ClipboardImageError('剪贴板中没有可读取的图片。')


def _save_linux(destination: Path) -> None:
    if shutil.which('wl-paste'):
        proc = _run(['wl-paste', '--no-newline', '--type', 'image/png'])
        if proc.returncode == 0 and proc.stdout:
            destination.write_bytes(proc.stdout)
            return
    if shutil.which('xclip'):
        proc = _run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'])
        if proc.returncode == 0 and proc.stdout:
            destination.write_bytes(proc.stdout)
            return
    raise ClipboardImageError('无法从 Linux 剪贴板读取图片。需要 Wayland 的 wl-paste 或 X11 的 xclip。')


def save_clipboard_image(destination: str | Path) -> str:
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass
    system = platform.system()
    try:
        if system == 'Darwin':
            _save_macos(path)
        elif system == 'Windows':
            _save_windows(path)
        else:
            _save_linux(path)
    except ClipboardImageError:
        raise
    except subprocess.TimeoutExpired as exc:
        raise ClipboardImageError('读取剪贴板超时。') from exc
    except Exception as exc:
        raise ClipboardImageError(f'读取剪贴板图片失败：{exc}') from exc
    if not path.exists() or path.stat().st_size == 0:
        raise ClipboardImageError('剪贴板图片保存失败。')
    return str(path)
