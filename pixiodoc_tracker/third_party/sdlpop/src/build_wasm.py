#!/usr/bin/env python3
"""Build SDLPoP to WebAssembly using Emscripten."""
import subprocess, sys, os
from pathlib import Path

EMSDK = Path(r"C:\Users\ander\AppData\Local\Temp\opencode\emsdk")
EMCC = str(EMSDK / "upstream" / "emscripten" / "emcc.bat")
SRC = Path(r"C:\Users\ander\OneDrive\Escritorio\juegoIO\juegoIO\pixiodoc_tracker\third_party\sdlpop\src")

os.chdir(SRC)

CFLAGS = [
    "-std=c99", "-O2", "-D_GNU_SOURCE=1", "-D__EMSCRIPTEN__",
    "-sUSE_SDL=2", "-sUSE_SDL_IMAGE=2",
]

FILES = [
    "main.c", "data.c", "seg000.c", "seg001.c", "seg002.c", "seg003.c",
    "seg004.c", "seg005.c", "seg006.c", "seg007.c", "seg008.c", "seg009.c",
    "seqtbl.c", "replay.c", "options.c", "lighting.c", "screenshot.c",
    "menu.c", "midi.c", "opl3.c", "stb_vorbis.c", "emscripten_bridge.c",
]

print("=== Cleaning old builds ===")
for f in list(Path(".").glob("*.o")) + ["prince.html", "prince.js", "prince.wasm", "prince.data"]:
    Path(f).unlink(missing_ok=True)

print("=== Compiling source files ===")
for src in FILES:
    obj = src.replace(".c", ".o")
    print(f"  {src} -> {obj}")
    r = subprocess.run([EMCC, src, "-c", "-o", obj] + CFLAGS)
    if r.returncode != 0:
        print(f"FAILED: {src}")
        sys.exit(1)

print("=== Linking WASM ===")
link_cmd = [EMCC] + [f for f in os.listdir(".") if f.endswith(".o")]
link_cmd += [
    "-sUSE_SDL=2", "-sUSE_SDL_IMAGE=2",
    '-sSDL2_IMAGE_FORMATS=["png"]',
    "-sALLOW_MEMORY_GROWTH=1",
    "-sASYNCIFY",
    "-sTOTAL_MEMORY=67108864",
    '-sEXPORTED_FUNCTIONS=["_main","_pop_set_hand_control","_pop_enable_hand_tracking","_pop_disable_hand_tracking","_pop_is_hand_tracking_active","_pop_get_current_level","_pop_get_remaining_minutes","_pop_get_remaining_ticks","_pop_get_hitpoints","_pop_get_kid_alive","_pop_is_game_over","_pop_get_next_level"]',
    '-sEXPORTED_RUNTIME_METHODS=["ccall","cwrap","FS","dynCall_vi","dynCall_vii","dynCall_viii"]',
    '-sDYNCALLS=1',
    "--preload-file", "../data@/data",
    "--shell-file", "shell.html",
    "-o", "prince.html",
    "-lm",
]

r = subprocess.run(link_cmd)
if r.returncode != 0:
    print("=== Build FAILED ===")
    sys.exit(1)
else:
    print("=== Build successful! ===")
    for f in ["prince.html", "prince.js", "prince.wasm", "prince.data"]:
        p = Path(f)
        if p.exists():
            print(f"  {f}: {p.stat().st_size} bytes")
