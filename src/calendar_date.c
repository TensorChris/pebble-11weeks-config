#include "calendar_date.h"

static int days_in_month(int year, int month) {
  static const int lengths[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  bool leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
  return lengths[month - 1] + (month == 2 && leap);
}

static void previous_day(CalendarDate *date) {
  date->weekday = (date->weekday + 6) % 7;
  if (--date->day == 0) {
    if (--date->month == 0) {
      date->month = 12;
      --date->year;
    }
    date->day = days_in_month(date->year, date->month);
  }
}

CalendarDate calendar_date_start(CalendarDate today, bool monday_first) {
  /* Anchor the view to the month containing seven calendar days before today. */
  for (int i = 0; i < 7; ++i) {
    previous_day(&today);
  }
  while (today.day != 1) {
    previous_day(&today);
  }
  int first_weekday = monday_first ? 1 : 0;
  while (today.weekday != first_weekday) {
    previous_day(&today);
  }
  return today;
}

void calendar_date_next(CalendarDate *date) {
  date->weekday = (date->weekday + 1) % 7;
  if (++date->day > days_in_month(date->year, date->month)) {
    date->day = 1;
    if (++date->month > 12) {
      date->month = 1;
      ++date->year;
    }
  }
}
