#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
typedef int32_t status_t;
typedef struct {int16_t x,y;} GPoint;
typedef struct {int16_t w,h;} GSize;
typedef struct {GPoint origin; GSize size;} GRect;
#define GPoint(x,y) ((GPoint){x,y})
#define GRect(x,y,w,h) ((GRect){{x,y},{w,h}})
typedef int GBitmapFormat;
typedef struct GBitmap {uint8_t *data; int w,h,stride,ox,oy,id; bool owns,mono;} GBitmap;
typedef struct {GBitmap frame; int op,fill,stroke,tx,ty;} GContext;
typedef struct Layer {GRect bounds; bool hidden,dirty; void (*draw)(struct Layer*,GContext*);} Layer;
typedef struct {int num_points; GPoint *points;} GPathInfo;
typedef struct {GPoint origin; int angle;} GPath;
#define GCompOpAssign 0
#define GCompOpSet 1
#define GColorBlack 0
#define GColorWhite 1
#define GColorBlackARGB8 0xc0
#define GCornerNone 0
#define TRIG_MAX_ANGLE 65536
#define APP_LOG(...)
#define RESOURCE_ID_IMAGE_BACKGROUND 1
#define RESOURCE_ID_IMAGE_NUMBER_3X5 2
#define RESOURCE_ID_IMAGE_BIG_NUMBER_3X5 3
#define RESOURCE_ID_IMAGE_CAP_LETTERS_3X5 4
#define RESOURCE_ID_IMAGE_QUIET_TIME 5
GBitmap *gbitmap_create_with_resource(int);
GBitmap *gbitmap_create_as_sub_bitmap(GBitmap*,GRect);
void gbitmap_destroy(GBitmap*);
GRect gbitmap_get_bounds(GBitmap*);
uint8_t *gbitmap_get_data(GBitmap*);
uint16_t gbitmap_get_bytes_per_row(GBitmap*);
GBitmapFormat gbitmap_get_format(GBitmap*);
void gbitmap_set_data(GBitmap*,uint8_t*,GBitmapFormat,uint16_t,bool);
GBitmap *graphics_capture_frame_buffer(GContext*);
void graphics_release_frame_buffer(GContext*,GBitmap*);
void graphics_context_set_compositing_mode(GContext*,int);
void graphics_context_set_fill_color(GContext*,int);
void graphics_context_set_stroke_color(GContext*,int);
void graphics_draw_bitmap_in_rect(GContext*,GBitmap*,GRect);
void graphics_draw_rect(GContext*,GRect);
void graphics_fill_rect(GContext*,GRect,int,int);
Layer *layer_create(GRect);
void layer_destroy(Layer*);
void layer_set_hidden(Layer*,bool);
void layer_mark_dirty(Layer*);
void host_draw_layer(Layer*,GContext*);
void host_write_frame(GContext*,const char*);
void layer_set_update_proc(Layer*,void (*)(Layer*,GContext*));
GPath *gpath_create(const GPathInfo*);
void gpath_destroy(GPath*);
void gpath_rotate_to(GPath*,int);
void gpath_move_to(GPath*,GPoint);
void gpath_draw_outline(GContext*,GPath*);
void gpath_draw_filled(GContext*,GPath*);
bool clock_is_24h_style(void);
status_t persist_write_int(uint32_t,int32_t);
int32_t persist_read_int(uint32_t);
/* Production time calls route through the researched Pebble model, not host mktime. */
struct tm *host_localtime(const time_t*);
time_t host_mktime(struct tm*);
#ifndef HOST_SHIM_IMPLEMENTATION
#define localtime host_localtime
#define mktime host_mktime
#endif
