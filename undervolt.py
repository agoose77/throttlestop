from plumbum import cmd
from getpass import getpass


def before(n):
    """Bits before n exclusive, indexing from 0"""
    return (1 << n) - 1


def from_(n):
    """Bits after n exclusive, indexing from 0"""
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


def parse_pkg_power_limit(MSR_PKG_POWER_LIMIT):
    power_1_limit = unit_power * (MSR_PKG_POWER_LIMIT & before(15))
    power_1_enabled = MSR_PKG_POWER_LIMIT >> 15 & before(1)
    power_1_clamping_limit = MSR_PKG_POWER_LIMIT >> 16 & before(1)
    power_1_power_limit_time_window = 2 ** ((MSR_PKG_POWER_LIMIT >> 17) & before(5)) * (
                1 + ((MSR_PKG_POWER_LIMIT >> 22) & before(2)) / 4) * unit_time
    return locals()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-u", "--undervolt", type=int)
    parser.add_argument("-t", "--maximum_tdp", type=int)
    args = parser.parse_args()

    sudo = cmd.sudo["-S"] << f"{getpass('Enter sudo password: ')}\n"
