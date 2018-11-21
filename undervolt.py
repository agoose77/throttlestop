from plumbum import cmd
from getpass import getpass
from types import SimpleNamespace


def before(n):
    """Bits before n exclusive, indexing from 0"""
    return (1 << n) - 1


def from_(n):
    """Bits after n inclusive, indexing from 0"""
    return ~before(n)


assert from_(2) & 0b100111 == 0b100100
assert before(5) & 0b1001101 == 0b01101


def read_msr(addr):
    addr_hex = hex(addr)
    result = sudo(cmd.rdmsr[addr_hex])
    return int(result.strip(), 16)


def write_msr(addr, value):
    addr_hex = hex(addr)
    value_hex = hex(value)
    return sudo[cmd.wrmsr[addr_hex, value_hex]]()


def parse_MSR_RAPL_POWER_UNIT(MSR_RAPL_POWER_UNIT):
    power = 1 / 2 ** (MSR_RAPL_POWER_UNIT & before(4))
    energy = 1 / 2 ** ((MSR_RAPL_POWER_UNIT >> 8) & before(5))
    time = 1 / 2 ** ((MSR_RAPL_POWER_UNIT >> 16) & before(4))
    return SimpleNamespace(**locals())


def _parse_MSR_PKG_POWER_LIMIT_internal(first, MSR_PKG_POWER_LIMIT, _units):
    if not first:
        MSR_PKG_POWER_LIMIT >>= 32

    power_limit = _units.power * (MSR_PKG_POWER_LIMIT & before(15))
    power_enabled = bool(MSR_PKG_POWER_LIMIT >> 15 & before(1))
    power_clamping_limit = bool(MSR_PKG_POWER_LIMIT >> 16 & before(1))
    power_power_limit_time_window = 2 ** ((MSR_PKG_POWER_LIMIT >> 17) & before(5)) * (
            1 + ((MSR_PKG_POWER_LIMIT >> 22) & before(2)) / 4) * _units.time
    return SimpleNamespace(**locals())


def parse_MSR_PKG_POWER_LIMIT(MSR_PKG_POWER_LIMIT, _units):
    first = _parse_MSR_PKG_POWER_LIMIT_internal(True, MSR_PKG_POWER_LIMIT, _units)
    second = _parse_MSR_PKG_POWER_LIMIT_internal(False, MSR_PKG_POWER_LIMIT, _units)
    return SimpleNamespace(**locals())


def build_MSR_PKG_POWER_LIMIT(power_1_limit, power_1_enabled, power_1_clamping_limit, power_1_power_limit_time_window):
    assert 10 <= power_1_limit <= 45
    MSR_PKG_POWER_LIMIT = read_msr(0x610)
    remainder = MSR_PKG_POWER_LIMIT & from_(24)
    head = MSR_PKG_POWER_LIMIT & before(24)
    head &= from_(15)
    head |= before(15) & int(30 / unit_power)
    new_msr = remainder | head
    new_msr


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-u", "--undervolt", type=int)
    parser.add_argument("-t", "--maximum_tdp", type=int)
    args = parser.parse_args()

    sudo = cmd.sudo["-S"] << f"{getpass('Enter sudo password: ')}\n"

    if args.t:
        MSR_RAPL_POWER_UNIT = read_msr(0x606)
        units = parse_MSR_RAPL_POWER_UNIT(MSR_RAPL_POWER_UNIT)

        MSR_PKG_POWER_LIMIT = read_msr(0x610)
        power_limits = parse_MSR_PKG_POWER_LIMIT(MSR_PKG_POWER_LIMIT, units)
