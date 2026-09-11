"""Contract-derived integration tests over the actual C calendar renderer."""
import datetime as dt
import hashlib
import json
import os
import shlex
from pathlib import Path
import subprocess
import tempfile
import unittest
from zoneinfo import ZoneInfo
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build' / 'contract-tests'
SHA = '3765d401a3861c90a4dce1d5f94c5ce27764bf9e140deaa9e8a2a25ae19c2e8e'
PLATFORMS = {'aplite': 'PBL_BW', 'basalt': 'PBL_COLOR', 'diorite': 'PBL_BW'}
MODELS = ('original', 'current')
ASSETS = ('background.png', 'number_3x5.png', 'big_number_3x5.png', 'cap_letters.png')


def prepare():
    BUILD.mkdir(parents=True, exist_ok=True)
    assert hashlib.sha256((ROOT / 'docs/contracts/calendar-weekday-v1.html').read_bytes()).hexdigest() == SHA
    definitions = ['typedef struct {int w,h; const unsigned char *data;} Asset;']
    sizes = []
    for i, name in enumerate(ASSETS):
        im = Image.open(ROOT / 'resources/images' / name).convert('RGB')
        pixels = [int(max(p) > 127) for p in im.getdata()]
        definitions.append(f'static const unsigned char asset_{i}[]={{' + ','.join(map(str, pixels)) + '};')
        sizes.append(f'{{{im.width},{im.height},asset_{i}}}')
    definitions.append('static const Asset assets[]={' + ','.join(sizes) + '};')
    (BUILD / 'assets.h').write_text('\n'.join(definitions))
    # Include later feature-local calendar modules without adding product skeletons.
    sources = sorted((ROOT / 'src').glob('calendar*.c')) + [ROOT / 'src' / f for f in ('numbers.c', 'letters.c', 'config.c')]
    for platform, mode in PLATFORMS.items():
        subprocess.run([os.environ.get('CC','cc'), *shlex.split(os.environ.get('CFLAGS','')), '-std=c11', '-D_DEFAULT_SOURCE', '-D_DARWIN_C_SOURCE', '-DNOLOG', f'-D{mode}',
                        f'-DPBL_PLATFORM_{platform.upper()}', '-Wall', '-Wextra', '-Wno-unused-parameter',
                        '-I'+str(ROOT/'tests/host'), '-I'+str(ROOT/'src'), '-I'+str(BUILD),
                        str(ROOT/'tests/host/runtime.c'), *map(str, sources), '-o', str(BUILD/platform)], check=True, capture_output=True)


def dates_for(today, monday=True):
    anchor = today - dt.timedelta(days=7)
    first = anchor.replace(day=1)
    start = first - dt.timedelta(days=(first.weekday() if monday else (first.weekday()+1)%7))
    return [start+dt.timedelta(days=i) for i in range(77)]


def render(local, zone='Europe/Berlin', monday=True, platform='aplite', model='current', flags=0,
           frames=1, toggle=False, reload=False, directory=None, style24=True):
    directory = directory or Path(tempfile.mkdtemp(prefix='case-', dir=BUILD))
    stamp = int(local.replace(tzinfo=ZoneInfo(zone)).timestamp())
    config = flags | (0 if monday else 16)
    env = dict(os.environ, TZ=zone, PEBBLE_TIME_MODEL=model)
    out = subprocess.run([str(BUILD/platform), str(directory), str(stamp), str(config), str(int(style24)),
                          str(frames), str(int(reload)), str(int(toggle))], env=env, capture_output=True, text=True, check=True)
    (directory/'trace.txt').write_text(out.stdout)
    result = []
    for part in out.stdout.split('FRAME ')[1:]:
        lines = part.splitlines()
        frame = {'image': Image.open(directory/f'frame-{lines[0]}.pgm').copy(), 'bitmaps': [], 'rects': [], 'directory': directory}
        for line in lines[1:]:
            typ, *values = line.split()
            values = list(map(int, values))
            if typ == 'BITMAP': frame['bitmaps'].append(values)
            elif typ == 'RECT': frame['rects'].append(values)
            elif typ == 'UNCHANGED': frame['unchanged'] = bool(values[0])
            elif typ == 'CONFIG': frame['config'] = values
        result.append(frame)
    return result


def digits_at(frame, x, y):
    return [b[1]//3 for b in frame['bitmaps'] if b[0]==2 and b[3]==x and b[4]==y]


def days_drawn(frame):
    result = []
    for row in range(11):
        for col in range(7):
            x, y = 26+14*col, 21+12*row
            tens, units = digits_at(frame,x,y), digits_at(frame,x+4,y)
            if len(units)!=1 or len(tens)>1: raise AssertionError(f'cell {row},{col}: tens={tens}, units={units}')
            result.append((tens[0]*10 if tens else 0)+units[0])
    return result


class CalendarContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls): prepare()

    def assert_calendar(self, frame, today, monday=True, check_pixels=True):
        dates = dates_for(today,monday)
        self.assertEqual(days_drawn(frame), [d.day for d in dates], '77 consecutive days in the chosen weekday columns')
        index = dates.index(today);row,col=divmod(index,7)
        self.assertEqual(len(frame['rects']),2,'Exactly one date marker and one header marker')
        date_mark,header_mark=frame['rects']
        self.assertEqual(date_mark[:4],[24+14*col,18+12*row,11,11])
        self.assertEqual(header_mark[:4],[23+14*col,9,13,9])
        headers = ['MO','TU','WE','TH','FR','SA','SU'] if monday else ['SU','MO','TU','WE','TH','FR','SA']
        for c, name in enumerate(headers):
            letters=[chr(b[1]//3+65) for b in frame['bitmaps'] if b[0]==4 and b[4]==11 and b[3] in (26+14*c,30+14*c)]
            self.assertEqual(''.join(letters),name)
        self.assertTrue(frame['unchanged'],'Renderer must not change current time inputs')
        # Month labels identify each row containing a month start.
        for r in range(11):
            row_dates=dates[r*7:(r+1)*7]
            names=''.join(chr(b[1]//3+65) for b in frame['bitmaps'] if b[0]==4 and b[3]>=124 and b[4]==21+12*r)
            firsts=[d for d in row_dates if d.day==1]
            self.assertEqual(names, firsts[0].strftime('%b').upper() if firsts else '')
            expected_year = row_dates[-1].year if r==0 else (firsts[0].year if firsts and firsts[0].month==1 else None)
            year_digits = [digits_at(frame,x,y) for x,y in ((11,18+12*r),(16,18+12*r),(11,24+12*r),(16,24+12*r))]
            if expected_year is not None:self.assertEqual(year_digits,[[int(n)] for n in str(expected_year)])
            else:self.assertTrue(all(not digits for digits in year_digits))
        if check_pixels:
            # Every actually drawn tiny glyph must also be present in the framebuffer.
            for resource,sx,sy,x,y,w,h in frame['bitmaps']:
                if resource not in (2,4):continue
                source=Image.open(ROOT/'resources/images'/ASSETS[resource-1]).convert('L').point(lambda p:255 if p>127 else 0)
                expected=source.crop((sx,sy,sx+w,sy+h))
                actual=frame['image'].crop((x,y,x+w,y+h))
                self.assertIn(actual.tobytes(),(expected.tobytes(),ImageOps.invert(expected).tobytes()),f'Visible glyph at {x},{y}')
            for x,y,w,h,color in frame['rects']:
                self.assertEqual(frame['image'].getpixel((x,y)),255*color)
                self.assertEqual(frame['image'].getpixel((x+w-1,y+h-1)),255*color)

    def test_KAL_01_reported_friday_and_week_37(self):
        for platform in PLATFORMS:
            for model in MODELS:
                with self.subTest(platform=platform,model=model):
                    frame=render(dt.datetime(2026,9,11,23,22),platform=platform,model=model)[0]
                    frame['image'].save(BUILD/f'reported-{platform}-{model}.png')
                    self.assert_calendar(frame,dt.date(2026,9,11))
                    self.assertEqual(days_drawn(frame)[7:14],list(range(7,14)))
                    self.assertEqual(digits_at(frame,6,33),[3]);self.assertEqual(digits_at(frame,11,33),[7])

    def test_KAL_02_month_year_and_gregorian_leap_boundaries(self):
        examples=[(2026,1,1),(2026,3,1),(2026,4,1),(2026,5,1),(2026,12,31),
                  (2024,2,29),(2000,2,29),(2100,3,1),(2027,1,7),(2026,8,7)]
        for date in examples:
            for monday in (True,False):
                for model in MODELS:
                    with self.subTest(date=date,monday=monday,model=model):
                        now=dt.datetime(*date,12)
                        self.assert_calendar(render(now,zone='UTC',monday=monday,model=model)[0],now.date(),monday)

    def test_KAL_03_switch_and_reload_persisted_week_start(self):
        now=dt.datetime(2026,9,11,13,27)
        for initial in (True,False):
            with self.subTest(initial=initial):
                frames=render(now,zone='UTC',monday=initial,frames=2,toggle=True)
                self.assert_calendar(frames[0],now.date(),initial)
                self.assert_calendar(frames[1],now.date(),not initial)
                after=render(now,zone='UTC',reload=True,directory=frames[0]['directory'])[0]
                self.assert_calendar(after,now.date(),not initial)
                self.assertEqual(after['config'][1],int(not initial))

    def test_KAL_04_all_hours_offsets_and_dst(self):
        cases=[('Europe/Berlin',(2026,9,11)),('Europe/Berlin',(2026,3,29)),
               ('Europe/Berlin',(2026,10,25)),('America/New_York',(2026,3,8)),
               ('America/New_York',(2026,11,1)),('Pacific/Kiritimati',(2026,9,11)),
               ('Pacific/Pago_Pago',(2026,9,11)),('Asia/Kathmandu',(2026,9,11))]
        for zone,date in cases:
            for hour in range(24):
                for monday in (True,False):
                    for model in MODELS:
                        now=dt.datetime(*date,hour,22)
                        # Skip nonexistent spring-forward wall times, never delivered by a clock.
                        zoned=now.replace(tzinfo=ZoneInfo(zone))
                        if dt.datetime.fromtimestamp(zoned.timestamp(),ZoneInfo(zone)).replace(tzinfo=None)!=now:continue
                        with self.subTest(zone=zone,now=now,monday=monday,model=model):
                            self.assert_calendar(render(now,zone=zone,monday=monday,model=model)[0],now.date(),monday,False)

    def test_KAL_04_next_minute_after_midnight(self):
        for zone,date in [('Europe/Berlin',(2026,9,11)),('Europe/Berlin',(2026,3,28)),
                          ('America/New_York',(2026,10,31)),('UTC',(2026,12,31))]:
            for monday in (True,False):
                for model in MODELS:
                    with self.subTest(zone=zone,date=date,monday=monday,model=model):
                        now=dt.datetime(*date,23,59)
                        frames=render(now,zone=zone,monday=monday,model=model,frames=2)
                        self.assert_calendar(frames[0],now.date(),monday)
                        self.assert_calendar(frames[1],now.date()+dt.timedelta(days=1),monday)

    def test_KAL_05_rendering_platforms_clock_and_options(self):
        for platform in PLATFORMS:
            for flags in (0,1,2,4,8,32,64,111):
                for style24 in (True,False):
                    with self.subTest(platform=platform,flags=flags,style24=style24):
                        now=dt.datetime(2026,9,11,13,27)
                        frame=render(now,zone='UTC',platform=platform,flags=flags,style24=style24)[0]
                        self.assert_calendar(frame,now.date())
                        self.assertEqual(frame['config'][2:],[int(bool(flags&b)) for b in (1,2,4,8,32,64)])
                        big=[(b[1]//42,b[3],b[4],b[5],b[6]) for b in frame['bitmaps'] if b[0]==3]
                        self.assertEqual(big,[(1 if style24 else 0,23,18,41,59),(3 if style24 else 1,79,18,41,59),(7,79,90,41,59),(2,23,90,41,59)])
                        background=[b for b in frame['bitmaps'] if b[0]==1]
                        self.assertEqual(background,[[1,0,0,0,0,144,168]])
                        week=digits_at(frame,6,33)+digits_at(frame,11,33)
                        self.assertEqual(week,[] if flags&64 else [3,7])

if __name__=='__main__':unittest.main(verbosity=2)
