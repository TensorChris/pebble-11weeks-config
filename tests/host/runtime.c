#define HOST_SHIM_IMPLEMENTATION
#include "pebble.h"
#include "calendar_layer.h"
#include "numbers.h"
#include "letters.h"
#include "config.h"
#include "assets.h"

static bool style24 = true;
static char persist_path[1024];
static struct tm local_buffer;

struct tm *host_localtime(const time_t *value) {
  localtime_r(value, &local_buffer);
  return &local_buffer;
}

/* Firmware semantics and the supported tm_isdst >= 0 domain: tests/README.md.
 * Host timegm normalizes Gregorian fields; localtime_r supplies timezone rules. */
time_t host_mktime(struct tm *value) {
  long offset = value->tm_gmtoff;
  int dst = value->tm_isdst;
  const char *model = getenv("PEBBLE_TIME_MODEL");
  bool original = model && !strcmp(model, "original");
  struct tm copy = *value;
  time_t result = timegm(&copy) - offset - (original && dst > 0 ? 3600 : 0);
  if (original) {
    gmtime_r(&result, value);
  } else {
    localtime_r(&result, value);
  }
  return result;
}

static int pixel(GBitmap *bitmap, int x, int y) {
  x += bitmap->ox;
  y += bitmap->oy;
  if (bitmap->mono) {
    return !!(bitmap->data[y * bitmap->stride + (x >> 3)] & (1 << (x & 7)));
  }
  return bitmap->data[y * bitmap->stride + x] != GColorBlackARGB8;
}

static void put(GContext *context, int x, int y, int value) {
  GBitmap *bitmap = &context->frame;
  if (x < 0 || y < 0 || x >= bitmap->w || y >= bitmap->h) return;
  if (bitmap->mono) {
    uint8_t *byte = &bitmap->data[y * bitmap->stride + (x >> 3)];
    uint8_t mask = 1 << (x & 7);
    *byte = value ? (*byte | mask) : (*byte & ~mask);
  } else {
    bitmap->data[y * bitmap->stride + x] = value ? 0xff : GColorBlackARGB8;
  }
}

GBitmap *gbitmap_create_with_resource(int id) {
  const Asset *asset = &assets[id - 1];
  GBitmap *bitmap = calloc(1, sizeof(*bitmap));
  bitmap->w = asset->w;
  bitmap->h = asset->h;
  bitmap->stride = (bitmap->w + 7) / 8;
  bitmap->mono = true;
  bitmap->owns = true;
  bitmap->id = id;
  bitmap->data = calloc(bitmap->stride * bitmap->h, 1);
  for (int y = 0; y < bitmap->h; y++) {
    for (int x = 0; x < bitmap->w; x++) {
      if (asset->data[y * bitmap->w + x]) {
        bitmap->data[y * bitmap->stride + (x >> 3)] |= 1 << (x & 7);
      }
    }
  }
  return bitmap;
}

GBitmap *gbitmap_create_as_sub_bitmap(GBitmap *bitmap, GRect rect) {
  GBitmap *sub = malloc(sizeof(*sub));
  *sub = *bitmap;
  sub->owns = false;
  sub->ox += rect.origin.x;
  sub->oy += rect.origin.y;
  sub->w = rect.size.w;
  sub->h = rect.size.h;
  return sub;
}

void gbitmap_destroy(GBitmap *bitmap) {
  if (bitmap->owns) free(bitmap->data);
  free(bitmap);
}

GRect gbitmap_get_bounds(GBitmap *bitmap) {
  return GRect(0, 0, bitmap->w, bitmap->h);
}

uint8_t *gbitmap_get_data(GBitmap *bitmap) { return bitmap->data; }
uint16_t gbitmap_get_bytes_per_row(GBitmap *bitmap) { return bitmap->stride; }
GBitmapFormat gbitmap_get_format(GBitmap *bitmap) { (void)bitmap; return 0; }

void gbitmap_set_data(GBitmap *bitmap, uint8_t *data, GBitmapFormat format,
                      uint16_t stride, bool owns) {
  (void)format;
  bitmap->data = data;
  bitmap->stride = stride;
  bitmap->owns = owns;
}

GBitmap *graphics_capture_frame_buffer(GContext *context) { return &context->frame; }
void graphics_release_frame_buffer(GContext *context, GBitmap *bitmap) {
  (void)context;
  (void)bitmap;
}
void graphics_context_set_compositing_mode(GContext *context, int mode) { context->op = mode; }
void graphics_context_set_fill_color(GContext *context, int color) { context->fill = color; }
void graphics_context_set_stroke_color(GContext *context, int color) { context->stroke = color; }

void graphics_draw_bitmap_in_rect(GContext *context, GBitmap *bitmap, GRect rect) {
  rect.origin.x += context->tx;
  rect.origin.y += context->ty;
  printf("BITMAP %d %d %d %d %d %d %d\n", bitmap->id, bitmap->ox, bitmap->oy,
         rect.origin.x, rect.origin.y, rect.size.w, rect.size.h);
  for (int y = 0; y < rect.size.h; y++) {
    for (int x = 0; x < rect.size.w; x++) {
      int value = pixel(bitmap, x, y);
      if (context->op == GCompOpSet) {
        value |= pixel(&context->frame, rect.origin.x + x, rect.origin.y + y);
      }
      put(context, rect.origin.x + x, rect.origin.y + y, value);
    }
  }
}

void graphics_draw_rect(GContext *context, GRect rect) {
  printf("RECT %d %d %d %d %d\n", rect.origin.x, rect.origin.y,
         rect.size.w, rect.size.h, context->stroke);
  for (int x = 0; x < rect.size.w; x++) {
    put(context, rect.origin.x + x, rect.origin.y, context->stroke);
    put(context, rect.origin.x + x, rect.origin.y + rect.size.h - 1, context->stroke);
  }
  for (int y = 0; y < rect.size.h; y++) {
    put(context, rect.origin.x, rect.origin.y + y, context->stroke);
    put(context, rect.origin.x + rect.size.w - 1, rect.origin.y + y, context->stroke);
  }
}

void graphics_fill_rect(GContext *context, GRect rect, int radius, int corners) {
  (void)radius;
  (void)corners;
  for (int y = 0; y < rect.size.h; y++) {
    for (int x = 0; x < rect.size.w; x++) {
      put(context, rect.origin.x + x, rect.origin.y + y, context->fill);
    }
  }
}

Layer *layer_create(GRect rect) {
  Layer *layer = calloc(1, sizeof(*layer));
  layer->bounds = rect;
  return layer;
}
void layer_destroy(Layer *layer) { free(layer); }
void layer_set_hidden(Layer *layer, bool hidden) { layer->hidden = hidden; }
void layer_mark_dirty(Layer *layer) { layer->dirty = true; }
void host_draw_layer(Layer *layer, GContext *context) {
  if (layer->hidden || !layer->dirty) return;
  context->tx = layer->bounds.origin.x;
  context->ty = layer->bounds.origin.y;
  layer->draw(layer, context);
  context->tx = context->ty = 0;
  layer->dirty = false;
}
void host_write_frame(GContext *context, const char *path) {
  FILE *file = fopen(path, "wb");
  if (!file) exit(4);
  fprintf(file, "P5\n144 168\n255\n");
  for (int y = 0; y < 168; y++) {
    for (int x = 0; x < 144; x++) fputc(pixel(&context->frame, x, y) ? 255 : 0, file);
  }
  fclose(file);
}
void layer_set_update_proc(Layer *layer, void (*draw)(Layer *, GContext *)) {
  layer->draw = draw;
}

GPath *gpath_create(const GPathInfo *info) {
  (void)info;
  return calloc(1, sizeof(GPath));
}
void gpath_destroy(GPath *path) { free(path); }
void gpath_rotate_to(GPath *path, int angle) { path->angle = angle; }
void gpath_move_to(GPath *path, GPoint origin) { path->origin = origin; }
void gpath_draw_outline(GContext *context, GPath *path) {
  int direction = path->angle ? -1 : 1;
  for (int x = 0; x < 3; x++) {
    put(context, path->origin.x - direction * x, path->origin.y - x, context->stroke);
    put(context, path->origin.x - direction * x, path->origin.y + x, context->stroke);
  }
}
void gpath_draw_filled(GContext *context, GPath *path) {
  int direction = path->angle ? -1 : 1;
  for (int x = 0; x < 3; x++) {
    for (int y = -x; y <= x; y++) {
      put(context, path->origin.x - direction * x, path->origin.y + y, context->fill);
    }
  }
}

bool clock_is_24h_style(void) { return style24; }
status_t persist_write_int(uint32_t key, int32_t value) {
  (void)key;
  FILE *file = fopen(persist_path, "wb");
  if (!file) return -1;
  fwrite(&value, sizeof(value), 1, file);
  fclose(file);
  return sizeof(value);
}
int32_t persist_read_int(uint32_t key) {
  (void)key;
  int32_t value = 0;
  FILE *file = fopen(persist_path, "rb");
  if (file) {
    fread(&value, sizeof(value), 1, file);
    fclose(file);
  }
  return value;
}

#ifndef HOST_LIBRARY
int main(int argc, char **argv) {
  if (argc != 8) return 2;
  snprintf(persist_path, sizeof(persist_path), "%s/config.bin", argv[1]);
  time_t timestamp = strtoll(argv[2], 0, 10);
  int flags = atoi(argv[3]);
  style24 = atoi(argv[4]);
  int frames = atoi(argv[5]);
  int reload = atoi(argv[6]);
  if (reload) {
    load_config(15);
  } else {
    set_config(flags);
    save_config(15);
  }
  GContext context = {0};
  context.frame.w = 144;
  context.frame.h = 168;
#ifdef PBL_BW
  context.frame.mono = true;
  context.frame.stride = 20;
#else
  context.frame.stride = 144;
#endif
  context.frame.data = calloc(context.frame.stride * context.frame.h, 1);
  numbers_create();
  letters_create();
  calendar_layer_create();
  for (int i = 0; i < frames; i++) {
    if (i && atoi(argv[7])) {
      set_config(get_config() ^ 16);
      save_config(15);
      calendar_layer_force_update();
    }
    struct tm now = *host_localtime(&timestamp);
    struct tm before = now;
    time_t before_t = timestamp;
    printf("FRAME %d\n", i);
    printf("CONFIG %d %d %d %d %d %d %d %d\n", get_config(), week_starts_monday(),
           hide_sec(), hide_frame(), hide_battery(), hide_bt_phone(),
           hide_quiet_time(), hide_week_numbers());
    memset(context.frame.data, context.frame.mono ? 0 : GColorBlackARGB8,
           context.frame.stride * context.frame.h);
    calendar_layer_update_time(&timestamp, &now);
    Layer *layer = calendar_layer_get_layer();
    layer->draw(layer, &context);
    printf("UNCHANGED %d\n", before_t == timestamp && !memcmp(&now, &before, sizeof(now)));
    char path[1024];
    snprintf(path, sizeof(path), "%s/frame-%d.pgm", argv[1], i);
    FILE *file = fopen(path, "wb");
    fprintf(file, "P5\n144 168\n255\n");
    for (int y = 0; y < 168; y++) {
      for (int x = 0; x < 144; x++) fputc(pixel(&context.frame, x, y) ? 255 : 0, file);
    }
    fclose(file);
    timestamp += 60;
  }
  calendar_layer_destroy();
  letters_destroy();
  numbers_destroy();
  free(context.frame.data);
  return 0;
}

#endif
