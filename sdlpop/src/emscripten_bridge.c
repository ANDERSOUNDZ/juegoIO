#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include "common.h"
#include "data.h"

static int hand_tracking_active = 0;
static sbyte hand_x = 0;
static sbyte hand_y = 0;
static sbyte hand_shift = 0;

EMSCRIPTEN_KEEPALIVE
void pop_enable_hand_tracking(void) {
    hand_tracking_active = 1;
}

EMSCRIPTEN_KEEPALIVE
void pop_disable_hand_tracking(void) {
    hand_tracking_active = 0;
}

EMSCRIPTEN_KEEPALIVE
int pop_is_hand_tracking_active(void) {
    return hand_tracking_active;
}

EMSCRIPTEN_KEEPALIVE
void pop_get_hand_control(int* x, int* y, int* shift) {
    if (x) *x = hand_x;
    if (y) *y = hand_y;
    if (shift) *shift = hand_shift;
}

EMSCRIPTEN_KEEPALIVE
void pop_set_hand_control(int x, int y, int shift) {
    hand_x = (sbyte)x;
    hand_y = (sbyte)y;
    hand_shift = shift ? CONTROL_HELD : CONTROL_RELEASED;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_current_level(void) {
    return current_level;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_remaining_minutes(void) {
    return rem_min;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_remaining_ticks(void) {
    return rem_tick;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_hitpoints(void) {
    return hitp_curr;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_kid_alive(void) {
    return Kid.alive;
}

EMSCRIPTEN_KEEPALIVE
int pop_is_game_over(void) {
    return (rem_min == 0 && current_level < 13) || Kid.alive > 6 ? 1 : 0;
}

EMSCRIPTEN_KEEPALIVE
int pop_get_next_level(void) {
    return next_level;
}

#endif
