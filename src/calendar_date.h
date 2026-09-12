#pragma once

#include <stdbool.h>

/* Local Gregorian date; month is 1..12, weekday is Sunday=0..Saturday=6. */
typedef struct {
  int year;
  int month;
  int day;
  int weekday;
} CalendarDate;

/* Inputs are valid local dates supplied by the clock adapter. */
CalendarDate calendar_date_start(CalendarDate today, bool monday_first);
void calendar_date_next(CalendarDate *date);
