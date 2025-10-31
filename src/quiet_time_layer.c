//
//  quiet_time_layer.c
//  pebble-watchface-11weeks
//
//  Created for v2.7
//  Displays moon icon when Quiet Time is active
//

#include "quiet_time_layer.h"
#include "const.h"

#define SPACING_X       2
#define SPACING_Y       -1
#define ICON_GAP        3  // Gap above watch battery icon

static Layer* s_layer = NULL;
static GBitmap* s_bitmap_quiet_time = NULL;
static bool s_quiet_time_active = false;

static void update_proc(Layer* layer, GContext* ctx);

static void update_proc(Layer* layer, GContext* ctx) {
  if (!s_quiet_time_active) {
    return;  // Don't draw if Quiet Time is not active
  }

  graphics_context_set_compositing_mode(ctx, GCompOpAssign);
  GRect rect = gbitmap_get_bounds(s_bitmap_quiet_time);
  graphics_draw_bitmap_in_rect(ctx, s_bitmap_quiet_time, rect);
}

void quiet_time_layer_create() {
  if (!s_bitmap_quiet_time) {
    s_bitmap_quiet_time = gbitmap_create_with_resource(RESOURCE_ID_IMAGE_QUIET_TIME);
  }

  if (!s_layer) {
    GRect rect = gbitmap_get_bounds(s_bitmap_quiet_time);
    // Position: above watch battery icon (bottom left), shifted 4px left
    rect.origin.x = SX - SPACING_X - 1 - rect.size.w - 4;
    rect.origin.y = SY + CH * WN + SPACING_Y - rect.size.h - ICON_GAP;
    s_layer = layer_create(rect);
    layer_set_update_proc(s_layer, update_proc);
  }
}

void quiet_time_layer_destroy() {
  if (s_bitmap_quiet_time) {
    gbitmap_destroy(s_bitmap_quiet_time);
    s_bitmap_quiet_time = NULL;
  }

  if (s_layer) {
    layer_destroy(s_layer);
    s_layer = NULL;
  }
}

Layer* quiet_time_layer_get_layer() {
  return s_layer;
}

void quiet_time_layer_update(bool is_quiet_time_active) {
  s_quiet_time_active = is_quiet_time_active;
}
