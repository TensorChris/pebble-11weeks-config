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
from urllib.parse import quote, unquote
import uuid
from zoneinfo import ZoneInfo

import png
from PIL import Image
from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.websocket import MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import (
    AppConfigSetup, AppConfigResponse, WebSocketPhonesimAppConfig,
    WebSocketPhonesimConfigResponse, WebSocketPhoneAppLog,
)
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
    sdk_header = sdk_root / 'sdk-core/pebble' / platform / 'include/pebble.h'
    quiet_api_stub = '#define quiet_time_is_active(...) (false)' in sdk_header.read_text()
    os.environ['PATH'] = str(sdk_root / 'toolchain/bin') + os.pathsep + os.environ['PATH']
    target = dt.datetime(2026, 9, 11, 23, 22, tzinfo=ZoneInfo('Europe/Berlin'))
    out = Path('build/runtime')
    out.mkdir(parents=True, exist_ok=True)
    transport = ManagedEmulatorTransport(platform, sdk, vnc_enabled=True)
    pebble = PebbleConnection(transport)
    failures = []
    acknowledgements = queue.Queue()
    configuration_evidence = []
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
                raise AssertionError('No phone-battery AppMessage acknowledgement') from None
            if tid == transaction and app == WATCHFACE:
                assert status == 'ack', 'Watchface rejected phone-battery AppMessage'
                return
        raise AssertionError('No phone-battery AppMessage acknowledgement')

    def open_config(timeout=15):
        replies = queue.Queue()
        handle = pebble.register_transport_endpoint(
            MessageTargetPhone, WebSocketPhonesimConfigResponse, replies.put)
        try:
            # JS readiness is acknowledged before this call. Send one Setup
            # only, so delayed callbacks cannot overlap a later save operation.
            pebble.transport.send_packet(
                WebSocketPhonesimAppConfig(config=AppConfigSetup()),
                target=MessageTargetPhone())
            try:
                response = replies.get(timeout=timeout)
            except queue.Empty:
                raise AssertionError('Real JS did not open configuration before timeout') from None
            url = response.config.data
            if isinstance(url, bytes):
                url = url.decode('utf-8')
            assert url.startswith('data:text/html'), 'JS did not open its real configuration page'
            return unquote(url.split(',', 1)[1])
        finally:
            pebble.unregister_endpoint(handle)

    def observe_js_logs():
        logs = queue.Queue()
        handle = pebble.register_transport_endpoint(
            MessageTargetPhone, WebSocketPhoneAppLog,
            lambda message: logs.put(message.payload))
        return logs, handle

    def wait_js_config_ack(logs, flags=None):
        prefix = 'Message sent successfully: {"KEY_CONFIG_VALUE":'
        expected = prefix if flags is None else prefix + str(flags) + '}'
        deadline = time.monotonic() + 15
        while True:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise AssertionError(f'No real JS AppMessage ACK for configuration {flags}')
            try:
                log = logs.get(timeout=remaining)
            except queue.Empty:
                raise AssertionError(f'No real JS AppMessage ACK for configuration {flags}') from None
            if isinstance(log, bytes):
                log = log.decode('utf-8', errors='replace')
            if expected in log:
                return
            if 'Message failed:' in log:
                raise AssertionError('Real JS AppMessage failed: ' + log)

    def assert_saved_config(flags, phase):
        html = open_config()
        assert f'var INJECTED_CONFIG={flags};' in html, (
            f'JS configuration was not preserved during {phase}: expected {flags}')
        configuration_evidence.append({'phase': phase, 'flags': flags, 'reopened_page': True})

    def config(flags, reset_clock=True):
        # Match the official emu-app-config lifecycle. Without Setup pypkjs
        # has no callback and ignores the response. The real webviewclosed JS
        # persists localStorage and sends key 6; a direct key 6 injection would
        # be overwritten by its ready handler after an app restart.
        open_config()
        logs, handle = observe_js_logs()
        try:
            response = quote(json.dumps({'config': flags}, separators=(',', ':')), safe="~()*!.'-")
            pebble.transport.send_packet(
                WebSocketPhonesimAppConfig(config=AppConfigResponse(data=response)),
                target=MessageTargetPhone())
            wait_js_config_ack(logs, flags)
            configuration_evidence.append({'phase': 'webviewclosed-ack', 'flags': flags})
        finally:
            pebble.unregister_endpoint(handle)
        assert_saved_config(flags, 'after-save')
        if reset_clock:
            settle()

    def run_app(app, start=True):
        command = AppRunStateStart(uuid=app) if start else AppRunStateStop(uuid=app)
        pebble.send_packet(AppRunState(data=command))

    def start_ready(flags):
        logs, handle = observe_js_logs()
        try:
            run_app(WATCHFACE)
            wait_js_config_ack(logs, flags)
            configuration_evidence.append({'phase': 'ready-ack', 'flags': flags})
        finally:
            pebble.unregister_endpoint(handle)

    def restart(flags):
        run_app(WATCHFACE, False)
        time.sleep(0.5)
        start_ready(flags)
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
        firmware_image = sdk_root / 'sdk-core/pebble' / platform / 'qemu/qemu_micro_flash.bin'
        metadata = {
            'platform': platform, 'sdk': sdk,
            'pebble_tool': importlib.metadata.version('pebble-tool'),
            'firmware_version': str(pebble.firmware_version),
            'firmware_sha256': hashlib.sha256(firmware_image.read_bytes()).hexdigest(),
            'pbw_sha256': hashlib.sha256(Path(pbw_path).read_bytes()).hexdigest(),
            'target_local': target.isoformat(),
            'timezone_scope': 'Fixed UTC+2 for this date; host tests cover DST rules',
            'quiet_time_api': 'constant false SDK macro' if quiet_api_stub else 'firmware API',
            'quiet_time_control': 'SDK shell has no toggle app or button handler; native OFF only',
            'quiet_time_on_evidence': 'Host executes original main.c callbacks and quiet_time_layer.c with controlled OS state',
            'sdk_header_sha256': hashlib.sha256(sdk_header.read_bytes()).hexdigest(),
        }
        (out / f'{platform}.json').write_text(json.dumps(metadata, indent=2))
        logs, handle = observe_js_logs()
        try:
            ToolAppInstaller(pebble, str(Path(pbw_path).resolve())).install()
            # Subscribe before install: ready can fire before install returns.
            # Its acknowledged config also proves that AppSync accepts messages.
            wait_js_config_ack(logs)
        finally:
            pebble.unregister_endpoint(handle)
        messages = AppMessageService(pebble)
        messages.register_handler('ack', lambda tid, app: acknowledgements.put(('ack', tid, app)))
        messages.register_handler('nack', lambda tid, app: acknowledgements.put(('nack', tid, app)))
        send_data_to_qemu(pebble.transport, QemuBattery(percent=73, charging=False))
        send_data_to_qemu(pebble.transport, QemuBluetoothConnection(connected=True))
        send_data_to_qemu(pebble.transport, QemuTimeFormat(is_24_hour=True))
        config(0)
        send({8: 0x70})
        settle()
        capture('friday', target)
        for flags, label in ((16, 'sunday'), (0, 'monday')):
            config(flags)
            capture(label, target, flags)
            restart(flags)
            assert_saved_config(flags, 'after-restart')
            capture(label + '-restart', target, flags)

        # The pinned SDK shell has no Settings/Quiet-Time toggle app or button
        # handler. Preserve its OFF state here; the host integration test runs
        # the exact main.c callbacks and real quiet layer with controlled ON/OFF.
        # https://github.com/coredevices/PebbleOS/blob/3b927684809fba173ee54029bdb32c6ae21611b5/src/fw/shell/sdk/system_app_registry_list.json
        require(not visible(capture('quiet-before'), 'quiet'), 'SDK Quiet Time must initially be off')
        enabled = capture('options-enabled', target)
        for region in REGIONS:
            if region == 'quiet':
                require(not visible(enabled, region), 'SDK Quiet Time must remain absent while OS state is off')
            else:
                require(visible(enabled, region), region + ' must be visible when enabled')
        for flag, region in ((1, 'seconds'), (2, 'frame'), (4, 'battery'),
                             (8, 'connection'), (32, 'quiet'), (64, 'week')):
            config(flag)
            hidden = capture('hidden-' + region, target, flag)
            require(not visible(hidden, region), region + ' must disappear after configuration')
            config(0)
            shown = capture('shown-' + region, target)
            if region == 'quiet':
                require(not visible(shown, region), 'Quiet Time option must preserve the SDK OS-off state')
            else:
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
            # Force a real option change below even when this mode was already
            # active; AppSync need not notify for an unchanged value.
            config(flags ^ 3)
            # Set time before apply_config subscribes its native tick timer.
            # A later clock jump would test firmware timer rescheduling instead
            # of the watchface's behavior at an ordinary midnight boundary.
            before_midnight = target.replace(hour=23, minute=59, second=45)
            set_clock(before_midnight)
            clock_started = time.monotonic()
            time.sleep(0.35)
            config(flags, reset_clock=False)
            capture('before-midnight-' + label, before_midnight, flags)
            setup_elapsed = time.monotonic() - clock_started
            assert setup_elapsed < 15, 'Midnight test setup did not finish before the day boundary'
            configuration_evidence.append({
                'phase': 'native-midnight', 'flags': flags,
                'initial_local': before_midnight.isoformat(),
                'setup_elapsed_seconds': setup_elapsed,
                'clock_updates_after_subscription': 0,
            })
            # No configuration, redraw, restart or clock update after this point:
            # the real firmware must deliver the day-changing tick itself.
            time.sleep(max(0, 17 - setup_elapsed))
            capture('midnight-' + label, before_midnight + dt.timedelta(seconds=15), flags)
        (out / f'{platform}-results.json').write_text(json.dumps({'failures': failures}, indent=2))
        assert not failures, '\n'.join(failures)
        print(f'{platform}: real PBW calendar, configuration, options, restart and midnight verified')
    except Exception as error:
        diagnostics = {'failures': failures, 'exception': str(error)}
        try:
            capture('failure')
        except Exception as screenshot_error:
            diagnostics['screenshot_exception'] = str(screenshot_error)
        (out / f'{platform}-results.json').write_text(json.dumps(diagnostics, indent=2))
        raise
    finally:
        try:
            (out / f'{platform}-configuration.json').write_text(
                json.dumps(configuration_evidence, indent=2))
        finally:
            if messages is not None:
                messages.shutdown()
            if getattr(transport, 'ws', None):
                transport.ws.close()
            subprocess.run(['pebble', 'kill'], check=False)


if __name__ == '__main__':
    main()
