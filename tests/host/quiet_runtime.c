/* Test-only integration of unchanged main.c callbacks with the real quiet layer.
 * Other status layers and OS services are boundary fakes; no quiet decisions
 * are reimplemented here. The callback source is extracted during test build. */
#include "pebble.h"
#include "config.h"
#include "calendar_layer.h"
#include "quiet_time_layer.h"

#define SECOND_UNIT 1
#define MINUTE_UNIT 2
typedef int TimeUnits;
typedef int BatteryChargeState;
typedef struct {
  void (*pebble_app_connection_handler)(bool);
  void (*pebblekit_connection_handler)(bool);
} ConnectionHandlers;

static Layer *s_calendar_layer, *s_sec_layer, *s_frame_layer;
static Layer *s_watch_battery_layer, *s_phone_battery_layer;
static Layer *s_bluetooth_layer, *s_quiet_time_layer;
static time_t s_now_t;
static struct tm s_now_tm;
static bool s_battery_api_supported;
static bool os_quiet_active;
static int os_quiet_reads;
static int subscribed_units;
static void (*subscribed_tick)(struct tm *, TimeUnits);
static void tick_handler(struct tm *, TimeUnits);
static void update_time(bool);

static void battery_handler(BatteryChargeState state) { (void)state; }
static void bt_handler(bool connected) { (void)connected; }
static ConnectionHandlers conn_handlers = {bt_handler, NULL};
static void battery_state_service_subscribe(void (*handler)(BatteryChargeState)) { (void)handler; }
static BatteryChargeState battery_state_service_peek(void) { return 100; }
static void battery_state_service_unsubscribe(void) {}
static void connection_service_subscribe(ConnectionHandlers handlers) { (void)handlers; }
static bool connection_service_peek_pebble_app_connection(void) { return true; }
static void connection_service_unsubscribe(void) {}
static void sec_layer_update_time(time_t *timestamp, struct tm *local) { (void)timestamp; (void)local; }
static void frame_layer_update_time(time_t *timestamp, struct tm *local) { (void)timestamp; (void)local; }
static bool quiet_time_is_active(void) {
  os_quiet_reads++;
  return os_quiet_active;
}
static void tick_timer_service_subscribe(TimeUnits units, void (*handler)(struct tm *, TimeUnits)) {
  subscribed_units = units;
  subscribed_tick = handler;
}

/* Complete exact bodies from src/main.c, generated with original #line locations. */
#include "quiet_main_functions.h"

int main(int argc, char **argv) {
  if (argc != 2) return 2;
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
  Layer placeholders[6] = {0};
  s_calendar_layer = &placeholders[0];
  s_sec_layer = &placeholders[1];
  s_frame_layer = &placeholders[2];
  s_watch_battery_layer = &placeholders[3];
  s_phone_battery_layer = &placeholders[4];
  s_bluetooth_layer = &placeholders[5];
  quiet_time_layer_create();
  s_quiet_time_layer = quiet_time_layer_get_layer();

  /* Active, hidden while active, visible again, OS off, OS on again.
   * Other status flags select minute-only ticking through real apply_config. */
  const int configs[] = {15, 47, 15, 15, 15};
  const bool os_states[] = {true, true, true, false, true};
  for (int frame = 0; frame < 5; frame++) {
    printf("FRAME %d\n", frame);
    set_config(configs[frame]);
    os_quiet_active = os_states[frame];
    os_quiet_reads = 0;
    apply_config();
    if (!subscribed_tick) return 3;
    subscribed_tick(&s_now_tm, subscribed_units);
    memset(context.frame.data, context.frame.mono ? 0 : GColorBlackARGB8,
           context.frame.stride * context.frame.h);
    host_draw_layer(s_quiet_time_layer, &context);
    printf("QUIET %d %d %d %d\n", os_quiet_active, s_quiet_time_layer->hidden,
           os_quiet_reads, subscribed_units);
    char path[1024];
    snprintf(path, sizeof(path), "%s/frame-%d.pgm", argv[1], frame);
    host_write_frame(&context, path);
  }
  quiet_time_layer_destroy();
  free(context.frame.data);
  return 0;
}
