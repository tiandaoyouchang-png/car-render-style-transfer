"""CLI discovery for GUI-launched Blender, without executing shell startup files."""
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path


def _apply_macos_system_proxy(env):
    """Give GUI-launched CLIs the same macOS proxy route as Terminal.

    Finder-launched Blender does not inherit shell proxy variables.  AGY can
    still read its Keychain token in that state, but its silent-auth network
    check times out and incorrectly falls back to browser OAuth.  Python's
    macOS proxy reader uses SystemConfiguration, so no shell startup files or
    credential stores are read here.  Existing environment values always win.
    """
    if sys.platform != "darwin":
        return
    try:
        proxies = urllib.request.getproxies()
    except (OSError, ValueError):
        return
    applied = False
    for scheme in ("http", "https"):
        lower, upper = f"{scheme}_proxy", f"{scheme.upper()}_PROXY"
        value = env.get(lower) or env.get(upper) or proxies.get(scheme)
        if not isinstance(value, str) or not value.strip():
            continue
        value = value.strip()
        env.setdefault(lower, value)
        env.setdefault(upper, value)
        applied = True
    if applied:
        bypass = env.get("no_proxy") or env.get("NO_PROXY") or proxies.get("no")
        if not isinstance(bypass, str) or not bypass.strip():
            bypass = "127.0.0.1,localhost"
        env.setdefault("no_proxy", bypass)
        env.setdefault("NO_PROXY", bypass)


def runtime_env(cli_path=""):
    env = dict(os.environ)
    # Finder-launched Blender may not inherit HOME even though Python can still
    # resolve Path.home() from the macOS account database.  AGY's Go runtime
    # requires the variable for its config, log and Keychain paths.
    try:
        home = Path.home()
    except RuntimeError:
        home = None
    if home is not None and not env.get("HOME"):
        env["HOME"] = str(home)
    _apply_macos_system_proxy(env)
    user_dir = home or Path.home()
    extra = [user_dir / ".local/bin", user_dir / ".bun/bin",
             user_dir / ".npm-global/bin", user_dir / ".volta/bin",
             Path("/opt/homebrew/bin"), Path("/usr/local/bin"),
             Path("/usr/bin"), Path("/bin")]
    for key in ("NVM_BIN", "VOLTA_HOME", "FNM_MULTISHELL_PATH"):
        if env.get(key):
            location = Path(env[key])
            extra.insert(0, location if key == "NVM_BIN" else location / "bin")
    if env.get("LOCALAPPDATA"):
        extra.append(Path(env["LOCALAPPDATA"]) / "agy/bin")
    if env.get("APPDATA"):
        extra.append(Path(env["APPDATA"]) / "npm")
    nvm_root = Path(env.get("NVM_DIR") or user_dir / ".nvm") / "versions/node"
    try:
        versions = sorted(nvm_root.glob("v*/bin"),
                          key=lambda p: tuple(int(n) for n in re.findall(r"\d+", p.parent.name)),
                          reverse=True)
        extra.extend(versions)
    except OSError:
        pass
    # Preserve the chosen launcher path (including symlinks); sibling node must
    # be discoverable when an explicitly selected CLI uses /usr/bin/env node.
    parts = ([str(Path(cli_path).absolute().parent)] if cli_path else [])
    parts += env.get("PATH", "").split(os.pathsep) + [str(p) for p in extra]
    seen = set()
    env["PATH"] = os.pathsep.join(p for p in parts if p and not (p in seen or seen.add(p)))
    env.setdefault("NO_COLOR", "1")
    return env


def find_cli(name, explicit_path="", env_keys=(), candidates=()):
    env = runtime_env()

    def resolve(value):
        value = os.path.expanduser(str(value or "").strip().strip('"'))
        if not value:
            return None
        found = shutil.which(value, path=env["PATH"])
        # Do not resolve symlinks: the launcher directory may contain node.
        return os.path.abspath(found) if found else None

    if str(explicit_path or "").strip():
        return resolve(explicit_path)  # explicit selection must not silently fall back
    for key in env_keys:
        if env.get(key):
            return resolve(env[key])
    found = resolve(name)
    if found:
        return found
    return next((hit for candidate in candidates if (hit := resolve(candidate))), None)
