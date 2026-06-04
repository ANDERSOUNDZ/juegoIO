# Build SDLPoP for WebAssembly with Emscripten
$ErrorActionPreference = "Stop"

$EMSDK = "C:\Users\ander\AppData\Local\Temp\opencode\emsdk"
$EMCC = "$EMSDK\upstream\emscripten\emcc.bat"

$SRC = "C:\Users\ander\OneDrive\Escritorio\juegoIO\juegoIO\pixiodoc_tracker\third_party\sdlpop\src"
Set-Location $SRC

$CFLAGS = "-std=c99 -O2 -D_GNU_SOURCE=1 -D__EMSCRIPTEN__ -sUSE_SDL=2 -sUSE_SDL_IMAGE=2"

$LDFLAGS = "-sUSE_SDL=2 -sUSE_SDL_IMAGE=2"
$LDFLAGS += " -sSDL2_IMAGE_FORMATS=`"[`"png`"]`""
$LDFLAGS += " -sALLOW_MEMORY_GROWTH=1"
$LDFLAGS += " -sASYNCIFY"
$LDFLAGS += " -sTOTAL_MEMORY=67108864"
$LDFLAGS += " -sEXPORTED_FUNCTIONS=`"[`"_main`",`"_pop_set_hand_control`",`"_pop_enable_hand_tracking`",`"_pop_disable_hand_tracking`",`"_pop_is_hand_tracking_active`",`"_pop_get_current_level`",`"_pop_get_remaining_minutes`",`"_pop_get_remaining_ticks`",`"_pop_get_hitpoints`",`"_pop_get_kid_alive`",`"_pop_is_game_over`",`"_pop_get_next_level`"]`""
$LDFLAGS += " -sEXPORTED_RUNTIME_METHODS=`"[`"ccall`",`"cwrap`",`"FS`"]`""
$LDFLAGS += " --preload-file $SRC\..\data"
$LDFLAGS += " --shell-file $SRC\shell.html"
$LDFLAGS += " -o prince.html"

Write-Host "=== Cleaning old builds ==="
Remove-Item -Force prince.html, prince.js, prince.wasm, prince.data -ErrorAction SilentlyContinue
Get-ChildItem *.o | Remove-Item -Force

Write-Host "=== Compiling source files ==="
$sources = @(
    "main.c", "data.c", "seg000.c", "seg001.c", "seg002.c", "seg003.c",
    "seg004.c", "seg005.c", "seg006.c", "seg007.c", "seg008.c", "seg009.c",
    "seqtbl.c", "replay.c", "options.c", "lighting.c", "screenshot.c",
    "menu.c", "midi.c", "opl3.c", "stb_vorbis.c", "emscripten_bridge.c"
)

foreach ($src in $sources) {
    $obj = $src -replace '\.c$', '.o'
    Write-Host "  Compiling $src -> $obj"
    $cmd = "`"$EMCC`" $src -c -o $obj $CFLAGS"
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to compile $src"
        exit 1
    }
}

Write-Host "=== Linking WASM ==="
$objFiles = (Get-ChildItem *.o | ForEach-Object { $_.Name }) -join " "
$cmd = "`"$EMCC`" $objFiles $LDFLAGS -lm"
Invoke-Expression $cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Build successful! ==="
    Get-ChildItem prince.html, prince.js, prince.wasm, prince.data | Select-Object Name, Length
} else {
    Write-Error "Link failed"
    exit 1
}
}

Write-Host "=== Linking WASM ==="
$objFiles = Get-ChildItem *.o | ForEach-Object { $_.Name }
$cmd = "emcc"
$cmd += $objFiles
$cmd += $LDFLAGS
$cmd += "-lm"
& $cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Build successful! ==="
    Get-ChildItem prince.html, prince.js, prince.wasm, prince.data | Select-Object Name, Length
} else {
    Write-Error "Link failed"
    exit 1
}
