import textwrap

from dfu_guide.detector import parse_system_profiler, parse_ioreg, DeviceState


def test_parse_system_profiler_dfu():
    sample = textwrap.dedent(
        """
        USB:

            Apple Mobile Device (DFU Mode):
                Product ID: 0x1227
                Vendor ID: 0x05ac (Apple Inc.)
        """
    )
    assert parse_system_profiler(sample) == DeviceState.DFU


def test_parse_system_profiler_recovery():
    sample = textwrap.dedent(
        """
        USB:

            Apple Mobile Device (Recovery Mode):
                Product ID: 0x1281
                Vendor ID: 0x05ac (Apple Inc.)
        """
    )
    assert parse_system_profiler(sample) == DeviceState.RECOVERY


def test_parse_system_profiler_normal():
    sample = textwrap.dedent(
        """
        USB:

            Apple Mobile Device:
                Product ID: 0x12a8
                Vendor ID: 0x05ac (Apple Inc.)
        """
    )
    assert parse_system_profiler(sample) == DeviceState.NORMAL


def test_parse_system_profiler_unknown():
    assert parse_system_profiler("") == DeviceState.UNKNOWN


def test_parse_ioreg_dfu():
    sample = textwrap.dedent(
        """
        +-o Apple Mobile Device (DFU Mode)@14200000  <class AppleUSBDevice, id 0x1000, registered, matched, active, busy 0 (278 ms), retain 11>
        """
    )
    assert parse_ioreg(sample) == DeviceState.DFU


def test_parse_ioreg_recovery():
    sample = textwrap.dedent(
        """
        +-o Apple Mobile Device (Recovery Mode)@14200000  <class AppleUSBDevice, id 0x1000>
        """
    )
    assert parse_ioreg(sample) == DeviceState.RECOVERY


def test_parse_ioreg_normal():
    sample = textwrap.dedent(
        """
        +-o Apple Mobile Device@14200000  <class AppleUSBDevice, id 0x1000>
        """
    )
    assert parse_ioreg(sample) == DeviceState.NORMAL
