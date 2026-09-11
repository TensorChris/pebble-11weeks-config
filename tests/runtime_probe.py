"""Run real PBW, configuration, persistence and pixels in a local emulator.

One connection owns time-setting and screenshots: reconnecting through the normal
CLI would synchronize the emulator to the host clock again.
"""
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import time
import uuid
from zoneinfo import ZoneInfo

import png
from PIL import Image
from libpebble2.communication import PebbleConnection
from libpebble2.protocol.apps import AppRunState, AppRunStateStart, AppRunStateStop
from libpebble2.protocol.system import TimeMessage, SetUTC
from libpebble2.services.appmessage import AppMessageService, Int32
from libpebble2.services.screenshot import Screenshot
from pebble_tool.commands.install import ToolAppInstaller
from pebble_tool.commands.emucontrol import send_data_to_qemu
from libpebble2.communication.transports.qemu.protocol import QemuBattery, QemuBluetoothConnection, QemuTimeFormat
from pebble_tool.sdk import sdk_manager
from pebble_tool.sdk.emulator import ManagedEmulatorTransport
from test_calendar import render

WATCHFACE = uuid.UUID('8ae4dd92-b5fa-42fa-aca9-d326dfad417f')
QUIET_TOGGLE = uuid.UUID('2220d805-cf9a-4e12-92b9-5ca778aff6bb')
REGIONS = {
    'seconds': (23, 153, 120, 158),
    'frame': (0, 0, 144, 3),
    'battery': (4, 149, 20, 161),
    'connection': (122, 150, 141, 162),
    'quiet': (8, 136, 16, 146),
    'week': (6, 33, 14, 38),
}


def main():
    platform, pbw_path = sys.argv[1:]
    sdk = '4.33.1'
    sdk_root = Path(sdk_manager.root_path_for_sdk(sdk))
    os.environ['PATH'] = str(sdk_root / 'toolchain/bin') + os.pathsep + os.environ['PATH']
    target = dt.datetime(2026, 9, 11, 23, 22, tzinfo=ZoneInfo('Europe/Berlin'))
    out = Path('build/runtime')
    out.mkdir(parents=True, exist_ok=True)
    transport = ManagedEmulatorTransport(platform, sdk, vnc_enabled=True)
    pebble = PebbleConnection(transport)
    failures = []
    acknowledgements = queue.Queue()
    messages = None

    def set_clock(local):
        pebble.send_packet(TimeMessage(message=SetUTC(
            unix_time=int(local.timestamp()),
            utc_offset=int(local.utcoffset().total_seconds() // 60), tz_name='UTC+2')))

    def settle():
        set_clock(target)
        time.sleep(0.35)
        set_clock(target)
        time.sleep(1.2)

    def send(values):
        transaction = messages.send_message(WATCHFACE, {key: Int32(value) for key, value in values.items()})
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                status, tid, app = acknowledgements.get(timeout=max(0.1, deadline-time.monotonic()))
            except queue.Empty:
                raise AssertionError('No configuration acknowledgement') from None
            if tid == transaction and app == WATCHFACE:
                assert status == 'ack', 'Watchface rejected configuration'
                return
        raise AssertionError('No configuration acknowledgement')

    def config(flags):
        send({6: flags})
        settle()

    def run_app(app, start=True):
        command = AppRunStateStart(uuid=app) if start else AppRunStateStop(uuid=app)
        pebble.send_packet(AppRunState(data=command))

    def restart():
        run_app(WATCHFACE, False)
        time.sleep(0.5)
        run_app(WATCHFACE)
        time.sleep(1)
        settle()

    def capture(label, expected_local=None, flags=0):
        path = out / f'{platform}-{label}.png'
        png.from_array(Screenshot(pebble).grab_image(), mode='RGB;8').save(str(path))
        actual = Image.open(path).convert('L').point(lambda p: 255 if p > 127 else 0)
        assert actual.size == (144, 168), 'Unexpected framebuffer size'
        if expected_local is not None:
            # UTC host rendering supplies the same wall-clock fields without the
            # known firmware normalization bug; its dates have a separate oracle.
            expected = render(expected_local.replace(tzinfo=None), zone='UTC',
                              platform=platform, monday=not bool(flags & 16), flags=flags)[0]['image']
            box = (23, 9, 121, 150)
            expected.save(out / f'{platform}-{label}-expected.png')
            if actual.crop(box).tobytes() != expected.crop(box).tobytes():
                failures.append(f'{platform}: {label} calendar pixels differ')
        return actual

    def visible(image, region):
        return image.crop(REGIONS[region]).getbbox() is not None

    def require(condition, label):
        if not condition:
            failures.append(f'{platform}: {label}')

    try:
        pebble.connect()
        pebble.run_async()
        time.sleep(5)
        ToolAppInstaller(pebble, str(Path(pbw_path).resolve())).install()
        messages = AppMessageService(pebble)
        messages.register_handler('ack', lambda tid, app: acknowledgements.put(('ack', tid, app)))
        messages.register_handler('nack', lambda tid, app: acknowledgements.put(('nack', tid, app)))
        send_data_to_qemu(pebble.transport, QemuBattery(percent=73, charging=False))
        send_data_to_qemu(pebble.transport, QemuBluetoothConnection(connected=True))
        send_data_to_qemu(pebble.transport, QemuTimeFormat(is_24_hour=True))
        config(0)
        send({8: 0x70})
        settle()
        firmware_image = sdk_root / 'sdk-core/pebble' / platform / 'qemu/qemu_micro_flash.bin'
        metadata = {
            'platform': platform, 'sdk': sdk,
            'pebble_tool': importlib.metadata.version('pebble-tool'),
            'firmware_version': str(pebble.firmware_version),
            'firmware_sha256': hashlib.sha256(firmware_image.read_bytes()).hexdigest(),
            'pbw_sha256': hashlib.sha256(Path(pbw_path).read_bytes()).hexdigest(),
            'target_local': target.isoformat(),
            'timezone_scope': 'Fixed UTC+2 for this date; host tests cover DST rules',
        }
        (out / f'{platform}.json').write_text(json.dumps(metadata, indent=2))
        capture('friday', target)
        for flags, label in ((16, 'sunday'), (0, 'monday')):
            config(flags)
            capture(label, target, flags)
            restart()
            capture(label + '-restart', target, flags)

        # Real OS quiet-time toggle, documented in PebbleOS system/toggle/quiet_time.
        baseline = capture('quiet-before')
        if not visible(baseline, 'quiet'):
            run_app(QUIET_TOGGLE)
            time.sleep(2.5)
            run_app(WATCHFACE)
            time.sleep(1.2)
            settle()
        enabled = capture('options-enabled', target)
        for region in REGIONS:
            require(visible(enabled, region), region + ' must be visible when enabled')
        for flag, region in ((1, 'seconds'), (2, 'frame'), (4, 'battery'),
                             (8, 'connection'), (32, 'quiet'), (64, 'week')):
            config(flag)
            hidden = capture('hidden-' + region, target, flag)
            require(not visible(hidden, region), region + ' must disappear after configuration')
            config(0)
            shown = capture('shown-' + region, target)
            require(visible(shown, region), region + ' must return after configuration')

        # Exercise the phone-battery alternative of the same existing option.
        send({8: 73})
        settle()
        require(visible(capture('phone-battery'), 'connection'), 'Phone battery must be visible')
        config(8)
        require(not visible(capture('phone-battery-hidden'), 'connection'), 'Phone battery must hide')
        config(0)
        send({8: 0x70})

        # Verify the native minute callback with both regular tick configurations.
        for flags, label in ((0, 'seconds-on'), (3, 'minute-only')):
            config(flags)
            before_midnight = target.replace(hour=23, minute=59, second=59)
            set_clock(before_midnight)
            time.sleep(2)
            capture('midnight-' + label, before_midnight + dt.timedelta(seconds=1), flags)
        (out / f'{platform}-results.json').write_text(json.dumps({'failures': failures}, indent=2))
        assert not failures, '\n'.join(failures)
        print(f'{platform}: real PBW calendar, configuration, options, restart and midnight verified')
    finally:
        if messages is not None:
            messages.shutdown()
        if getattr(transport, 'ws', None):
            transport.ws.close()
        subprocess.run(['pebble', 'kill'], check=False)


if __name__ == '__main__':
    main()
