@echo off
REM Build SDLPoP for WebAssembly with Emscripten

set EMSDK=C:\Users\ander\AppData\Local\Temp\opencode\emsdk
set EMCC=%EMSDK%\upstream\emscripten\emcc.bat

set SRC=C:\Users\ander\OneDrive\Escritorio\juegoIO\juegoIO\sdlpop\src
cd /d %SRC%

set CFLAGS=-std=c99 -O2 -D_GNU_SOURCE=1 -D__EMSCRIPTEN__ -sUSE_SDL=2 -sUSE_SDL_IMAGE=2

echo === Cleaning old builds ===
if exist prince.html del prince.html
if exist prince.js del prince.js
if exist prince.wasm del prince.wasm
if exist prince.data del prince.data
del *.o 2>nul

echo === Compiling source files ===
call %EMCC% main.c -c -o main.o %CFLAGS%
call %EMCC% data.c -c -o data.o %CFLAGS%
call %EMCC% seg000.c -c -o seg000.o %CFLAGS%
call %EMCC% seg001.c -c -o seg001.o %CFLAGS%
call %EMCC% seg002.c -c -o seg002.o %CFLAGS%
call %EMCC% seg003.c -c -o seg003.o %CFLAGS%
call %EMCC% seg004.c -c -o seg004.o %CFLAGS%
call %EMCC% seg005.c -c -o seg005.o %CFLAGS%
call %EMCC% seg006.c -c -o seg006.o %CFLAGS%
call %EMCC% seg007.c -c -o seg007.o %CFLAGS%
call %EMCC% seg008.c -c -o seg008.o %CFLAGS%
call %EMCC% seg009.c -c -o seg009.o %CFLAGS%
call %EMCC% seqtbl.c -c -o seqtbl.o %CFLAGS%
call %EMCC% replay.c -c -o replay.o %CFLAGS%
call %EMCC% options.c -c -o options.o %CFLAGS%
call %EMCC% lighting.c -c -o lighting.o %CFLAGS%
call %EMCC% screenshot.c -c -o screenshot.o %CFLAGS%
call %EMCC% menu.c -c -o menu.o %CFLAGS%
call %EMCC% midi.c -c -o midi.o %CFLAGS%
call %EMCC% opl3.c -c -o opl3.o %CFLAGS%
call %EMCC% stb_vorbis.c -c -o stb_vorbis.o %CFLAGS%
call %EMCC% emscripten_bridge.c -c -o emscripten_bridge.o %CFLAGS%

echo === Linking WASM ===
set LDFLAGS=-sUSE_SDL=2 -sUSE_SDL_IMAGE=2
set LDFLAGS=%LDFLAGS% -sSDL2_IMAGE_FORMATS="[^"png^"]"
set LDFLAGS=%LDFLAGS% -sALLOW_MEMORY_GROWTH=1
set LDFLAGS=%LDFLAGS% -sASYNCIFY
set LDFLAGS=%LDFLAGS% -sTOTAL_MEMORY=67108864
set LDFLAGS=%LDFLAGS% -sEXPORTED_FUNCTIONS="[^"_main^",^"_pop_set_hand_control^",^"_pop_enable_hand_tracking^",^"_pop_disable_hand_tracking^",^"_pop_is_hand_tracking_active^",^"_pop_get_current_level^",^"_pop_get_remaining_minutes^",^"_pop_get_remaining_ticks^",^"_pop_get_hitpoints^",^"_pop_get_kid_alive^",^"_pop_is_game_over^",^"_pop_get_next_level^"]"
set LDFLAGS=%LDFLAGS% -sEXPORTED_RUNTIME_METHODS="[^"ccall^",^"cwrap^",^"FS^"]"
set LDFLAGS=%LDFLAGS% --preload-file ..\data
set LDFLAGS=%LDFLAGS% --shell-file shell.html
set LDFLAGS=%LDFLAGS% -o prince.html

call %EMCC% *.o %LDFLAGS% -lm

if errorlevel 1 (
    echo === Build FAILED ===
    exit /b 1
) else (
    echo === Build successful! ===
    dir prince.html prince.js prince.wasm prince.data
)
