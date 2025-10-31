//
//  quiet_time_layer.h
//  pebble-watchface-11weeks
//
//  Created for v2.7
//  Displays moon icon when Quiet Time is active
//

#ifndef quiet_time_layer_h
#define quiet_time_layer_h

#include "necessary.h"

void quiet_time_layer_create();
void quiet_time_layer_destroy();
Layer* quiet_time_layer_get_layer();
void quiet_time_layer_update(bool is_quiet_time_active);

#endif /* quiet_time_layer_h */
