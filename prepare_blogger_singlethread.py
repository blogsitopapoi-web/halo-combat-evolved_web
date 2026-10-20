#!/usr/bin/env python3
"""Prepare an experimental single-threaded OpenCE web build.

Run against a checkout of OpenCE. This does not rewrite a prebuilt halo.wasm;
OpenCE must be recompiled afterwards. The script is deliberately strict: if
its expected source patterns differ, it aborts rather than making a partial
or unsafe edit.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def edit_web_build(path: Path) -> str:
    text = path.read_text(encoding="utf-8")

    # Remove pthreads from compile flags, but only inside WEB_ABI_FLAGS.
    pattern = r'(WEB_ABI_FLAGS\s*=\s*\[)(.*?)(\n\])'
    match = re.search(pattern, text, flags=re.S)
    if not match:
        raise RuntimeError("Could not find WEB_ABI_FLAGS in tools/web_build.py")
    block = match.group(2)
    if '"-pthread"' not in block:
        raise RuntimeError("WEB_ABI_FLAGS does not contain the expected -pthread flag")
    block = block.replace('    "-pthread",\n', '', 1)
    text = text[:match.start(2)] + block + text[match.end(2):]

    text = replace_once(
        text,
        'command=f"echo \'#include <SDL3/SDL.h>\' > $out.c && $web_emcc {sdl_flag} -pthread -c $out.c -o $out.o && "',
        'command=f"echo \'#include <SDL3/SDL.h>\' > $out.c && $web_emcc {sdl_flag} -c $out.c -o $out.o && "',
        "SDL port compile flags",
    )
    text = replace_once(
        text,
        '"-O2", "-g2", "-pthread", sdl_flag,',
        '"-O2", "-g2", sdl_flag,',
        "link pthread flag",
    )

    # These options are only valid/needed for Emscripten pthread builds.
    for line, label in [
        ('        "-sPROXY_TO_PTHREAD=1",\n', "PROXY_TO_PTHREAD"),
        ('        "-sPTHREAD_POOL_SIZE=16",\n', "PTHREAD_POOL_SIZE"),
        ('        "-sOFFSCREENCANVAS_SUPPORT=1",\n', "OFFSCREENCANVAS_SUPPORT"),
        ('        "-sOFFSCREENCANVASES_TO_PTHREAD=#canvas",\n', "OFFSCREENCANVASES_TO_PTHREAD"),
        ('        "-sDEFAULT_PTHREAD_STACK_SIZE=2MB",\n', "DEFAULT_PTHREAD_STACK_SIZE"),
    ]:
        text = replace_once(text, line, "", label)

    return text


def edit_app_js(path: Path) -> str:
    text = path.read_text(encoding="utf-8")

    # The single-thread experiment must not try to install isolation headers.
    text, count = re.subn(
        r'async function isolate\(\) \{.*?\n\}',
        "async function isolate() {\n  // Single-thread experiment: SharedArrayBuffer and COOP/COEP are not required.\n}",
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("Could not replace isolate() in app.js")

    text = replace_once(
        text,
        'new WebAssembly.Memory({ initial: pages, maximum: pages, shared: true });',
        'new WebAssembly.Memory({ initial: pages, maximum: pages });',
        "non-shared WebAssembly memory check",
    )
    text = replace_once(
        text,
        "  addCheck('isolated', window.crossOriginIsolated ? 'good' : 'bad', 'Threads (cross-origin isolation)',\n"
        "    window.crossOriginIsolated ? '' : 'reload the page; a private window may not allow it');\n",
        "",
        "isolation browser check",
    )
    text = replace_once(
        text,
        "  const webgl = typeof OffscreenCanvas !== 'undefined' && await workerWebGL2();",
        "  const webglCanvas = document.createElement('canvas');\n"
        "  const webgl = !!webglCanvas.getContext('webgl2');",
        "main-thread WebGL2 browser check",
    )
    text = replace_once(
        text,
        '  addCheck(\'webgl\', webgl ? \'good\' : \'bad\', \'WebGL 2 from a worker\');',
        '  addCheck(\'webgl\', webgl ? \'good\' : \'bad\', \'WebGL 2\');',
        "WebGL2 check label",
    )
    text = replace_once(
        text,
        '  const memory = window.crossOriginIsolated && memoryAvailable();',
        '  const memory = memoryAvailable();',
        "memory check",
    )
    text = replace_once(
        text,
        "  const required = ['secure', 'isolated', 'webgl', 'opfs', 'memory'];",
        "  const required = ['secure', 'webgl', 'opfs', 'memory'];",
        "required browser checks",
    )
    return text


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: prepare_blogger_singlethread.py PATH_TO_OPEN_CE_CHECKOUT", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    web_build = root / "tools" / "web_build.py"
    app_js = root / "port" / "web" / "site" / "app.js"
    missing = [str(p) for p in (web_build, app_js) if not p.is_file()]
    if missing:
        print("OpenCE checkout is missing expected files:\n" + "\n".join(missing), file=sys.stderr)
        return 2
    try:
        # Prepare both edits in memory first so a pattern mismatch cannot leave
        # the source checkout half-patched.
        patched_web_build = edit_web_build(web_build)
        patched_app_js = edit_app_js(app_js)
    except Exception as exc:
        print(f"Patch failed safely; no source files were changed: {exc}", file=sys.stderr)
        return 1
    web_build.write_text(patched_web_build, encoding="utf-8")
    app_js.write_text(patched_app_js, encoding="utf-8")
    print("Patched OpenCE for an experimental non-pthread web build.")
    print("This is a build experiment, not yet a verified Blogger-native port.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
