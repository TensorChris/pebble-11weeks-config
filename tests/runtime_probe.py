"""KAL-01/04/05: run the real PBW and minute tick in a local headless emulator.

Uses one connection for setting time and capturing pixels: the normal CLI's
emulator reconnect would otherwise reset the clock to the current host time.
"""
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

import png
from PIL import Image
from libpebble2.communication import PebbleConnection
from libpebble2.protocol.system import TimeMessage, SetUTC
from libpebble2.services.screenshot import Screenshot
from pebble_tool.commands.install import ToolAppInstaller
from pebble_tool.sdk import sdk_manager
from pebble_tool.sdk.emulator import ManagedEmulatorTransport
from test_calendar import render


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

    def set_clock(local):
        packet = TimeMessage(message=SetUTC(
            unix_time=int(local.timestamp()),
            utc_offset=int(local.utcoffset().total_seconds() // 60), tz_name='UTC+2'))
        pebble.send_packet(packet)

    def capture(label, expected_local):
        image_path = out / f'{platform}-{label}.png'
        png.from_array(Screenshot(pebble).grab_image(), mode='RGB;8').save(str(image_path))
        actual = Image.open(image_path).convert('L').point(lambda p: 255 if p > 127 else 0)
        expected = render(expected_local.replace(tzinfo=None), platform=platform)[0]['image']
        assert actual.size == (144, 168), 'Unexpected framebuffer size'
        # Full header and date-grid pixels, excluding unrelated animated border,
        # battery and seconds areas. Host expectations pass independent date tests.
        box = (23, 9, 121, 150)
        expected.save(out / f'{platform}-{label}-expected.png')
        assert actual.crop(box).tobytes() == expected.crop(box).tobytes(), f'{platform}: {label} calendar pixels differ'

    try:
        pebble.connect()
        pebble.run_async()
        time.sleep(5)
        ToolAppInstaller(pebble, str(Path(pbw_path).resolve())).install()
        set_clock(target)
        time.sleep(0.35)
        set_clock(target)
        time.sleep(1)
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
        before_midnight = target.replace(hour=23, minute=59, second=59)
        set_clock(before_midnight)
        time.sleep(2)
        capture('midnight', (before_midnight + dt.timedelta(seconds=1)))
        print(f'{platform}: real PBW Friday and midnight pixels verified')
    finally:
        if getattr(transport, 'ws', None):
            transport.ws.close()
        subprocess.run(['pebble', 'kill'], check=False)


if __name__ == '__main__':
    main()
