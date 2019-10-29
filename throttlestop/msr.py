from numbers import Real
from types import SimpleNamespace

import numpy as np
from plumbum import cmd, local, CommandNotFound, RETCODE

MSR_PKG_POWER_LIMIT_ADDR = 0x610
MSR_RAPL_POWER_UNIT_ADDR = 0x606
MSR_VOLTAGE_ADDR = 0x150
MSR_TEMPERATURE_TARGET_ADDR = 0x1A2

MSR_VOLTAGE_PLANES = {
    'cpu': 0,
    'gpu': 1,
    'cache': 2,
    'agent': 3,
    'analog_io': 4,
}


def before(n):
    """Bits before n exclusive, indexing from 0"""
    return (1 << n) - 1


def from_(n):
    """Bits after n inclusive, indexing from 0"""
    return ~before(n)


assert from_(2) & 0b100111 == 0b100100
assert before(5) & 0b1001101 == 0b01101


class MSR:

    def __init__(self, password=None):
        self.password = password

    @staticmethod
    def validate_install(test_address: str):
        """Ensure that the MSR tools and kernel module have been correctly loaded. Raise `RuntimeError` if not.

        :param test_address: readable MSR address
        """
        try:
            rdmsr = local['rdmsr']
        except CommandNotFound:
            raise RuntimeError("Cannot find `rdmsr`. Have you installed `msr-tools`?")

        if rdmsr[test_address] & RETCODE:
            raise RuntimeError("`rdmsr` call failed. Have you loaded the `msr` module with `modprobe msr`?")

    def _run_command(self, command):
        if self.password is None:
            return command()
        sudo = (cmd.sudo["-S"] << f"{self.password}\n")
        return sudo(command)

    def read(self, addr):
        addr_hex = hex(addr)
        result = self._run_command(cmd.rdmsr[addr_hex])
        return int(result.strip(), 16)

    def write(self, addr, value):
        addr_hex = hex(addr)
        value_hex = hex(value)
        return self._run_command(cmd.wrmsr[addr_hex, value_hex])


def parse_MSR_RAPL_POWER_UNIT(MSR_RAPL_POWER_UNIT):
    power = 1 / 2 ** (MSR_RAPL_POWER_UNIT & before(4))
    energy = 1 / 2 ** ((MSR_RAPL_POWER_UNIT >> 8) & before(5))
    time = 1 / 2 ** ((MSR_RAPL_POWER_UNIT >> 16) & before(4))
    return SimpleNamespace(**locals())


def _parse_MSR_PKG_POWER_LIMIT_internal(MSR_PKG_POWER_LIMIT, _units):
    power_limit = _units.power * (MSR_PKG_POWER_LIMIT & before(15))
    power_enabled = bool(MSR_PKG_POWER_LIMIT >> 15 & before(1))
    power_clamping_limit = bool(MSR_PKG_POWER_LIMIT >> 16 & before(1))
    power_limit_time_window = 2 ** ((MSR_PKG_POWER_LIMIT >> 17) & before(5)) * (
            1 + ((MSR_PKG_POWER_LIMIT >> 22) & before(2)) / 4) * _units.time
    return SimpleNamespace(**locals())


def parse_MSR_PKG_POWER_LIMIT(MSR_PKG_POWER_LIMIT, _units):
    first = _parse_MSR_PKG_POWER_LIMIT_internal(MSR_PKG_POWER_LIMIT, _units)
    second = _parse_MSR_PKG_POWER_LIMIT_internal(MSR_PKG_POWER_LIMIT >> 32, _units)
    lock = bool(MSR_PKG_POWER_LIMIT & (1 << 63))
    return SimpleNamespace(**locals())


def build_MSR_PKG_POWER_LIMIT(_obj, _units, _max_power_limit=60):
    assert isinstance(_obj.lock, bool)
    result = _build_MSR_PKG_POWER_LIMIT_internal(_obj.first, _units, _max_power_limit)
    result |= _build_MSR_PKG_POWER_LIMIT_internal(_obj.second, _units, _max_power_limit) << 32
    result |= int(_obj.lock) << 63
    return result


def _build_MSR_PKG_POWER_LIMIT_internal(_obj, _units, _max_power_limit):
    assert isinstance(_obj.power_limit, Real), _obj.power_limit
    assert isinstance(_obj.power_clamping_limit, bool), _obj.power_clamping_limit
    assert isinstance(_obj.power_enabled, bool), _obj.power_enabled
    assert isinstance(_obj.power_limit_time_window, Real), _obj.power_limit_time_window
    assert 0. <= _obj.power_limit <= _max_power_limit, _obj.power_limit
    assert _obj.power_limit_time_window > 0.

    value = before(15) & int(_obj.power_limit / _units.power)
    value |= int(_obj.power_enabled) << 15
    value |= int(_obj.power_clamping_limit) << 16

    k, y = determine_k_y(_obj.power_limit_time_window / _units.time)
    value |= before(24) & ((k << 5 | y) << 17)
    return value


def determine_k_y(p):
    """where p has no units"""
    k = np.arange(4)
    f = 1 + k / 4

    # Evaluate for all k the y values
    y = (np.log(p) - np.log(f)) / np.log(2)

    # Determine the extrema (floor and ceil)
    y_min = np.floor(y[-1]).astype(np.int_)
    y_max = np.ceil(y[0]).astype(np.int_)

    # Find the parameters which minimise the error
    error = np.inf
    solution = None
    for i, yi in enumerate(range(y_min, y_max + 1)):
        for j, fi in enumerate(f):
            dp = np.abs(2 ** yi * fi - p)
            if dp < error:
                error = dp
                solution = k[j], yi
    return solution


def _calculate_voltage_offset(voltage):
    assert -1023 <= voltage <= 1024
    rounded_offset = round(1.024 * voltage)
    return 0xFFE00000 & ((rounded_offset & 0xFFF) << 21)


def parse_MSR_UNDERVOLTAGE(value):
    x = (value >> 21)
    return (x if x <= 1024 else (x - 2048)) / 1.024


def build_MSR_VOLTAGE(obj, allow_overvoltage=False):
    assert obj.plane in MSR_VOLTAGE_PLANES.values()
    if obj.voltage is not None:
        assert isinstance(obj.voltage, int), obj.voltage
        if not allow_overvoltage:
            assert obj.voltage <= 0

        offset = _calculate_voltage_offset(obj.voltage)
    else:
        offset = None

    return 1 << 63 | (obj.plane << 32 + 4 + 4) | (1 << (32 + 4)) | ((offset is not None) << 32) | \
           (offset or 0)

def parse_MSR_TEMPERATURE_TARGET(MSR_TEMPERATURE_TARGET):
    offset = (MSR_TEMPERATURE_TARGET & before(30)) >> 24
    base = (MSR_TEMPERATURE_TARGET & before(24)) >> 16
    tau = MSR_TEMPERATURE_TARGET & before(7)
    return SimpleNamespace(**locals())

def build_MSR_TEMPERATURE_TARGET(_obj):
    assert 0 <= _obj.offset < _obj.base, f"Target must lie in interval [0, {_obj.base})"
    assert 20 < _obj.base <= 100, f"Target must be above approximate room temperature, not {_obj.base}"
    assert _obj.tau < 2**6-1, f"Tau can only fit within 6 bits, {_obj.tau} is too large"
    value = _obj.tau
    value |= _obj.offset << 24
    return value
