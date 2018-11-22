from json import dumps, loads
from types import SimpleNamespace

from throttlestop.msr import MSR, parse_MSR_PKG_POWER_LIMIT, parse_MSR_RAPL_POWER_UNIT, build_MSR_PKG_POWER_LIMIT, \
    MSR_PKG_POWER_LIMIT_ADDR, MSR_RAPL_POWER_UNIT_ADDR, MSR_VOLTAGE_ADDR, parse_MSR_UNDERVOLTAGE, build_MSR_VOLTAGE
from throttlestop.tools import NamespaceEncoder, namespace_object_hook


def apply_delta(delta: dict, ns: SimpleNamespace):
    assert isinstance(delta, dict)
    assert isinstance(ns, SimpleNamespace)

    for key, value in delta.items():
        if isinstance(value, dict):
            obj = getattr(ns, key)
            apply_delta(value, obj)
        else:
            setattr(ns, key, value)


def load_json_delta(string):
    return loads(string, object_hook=namespace_object_hook)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    tdp_parser = subparsers.add_parser('tdp')
    group = tdp_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--read", dest="read_tdp", action='store_true')
    group.add_argument("-w", "--write", dest="write_tdp", type=load_json_delta)

    voltage_parser = subparsers.add_parser('voltage')
    voltage_parser.add_argument("voltage_plane", type=int)
    voltage_parser.add_argument("-v", "--value", dest="voltage_value", type=int)

    args = parser.parse_args()

    msr = MSR()

    read_tdp = getattr(args, 'read_tdp', None)
    write_tdp = getattr(args, 'write_tdp', None)
    voltage_plane = getattr(args, 'voltage_plane', None)
    voltage_value = getattr(args, 'voltage_value', None)

    if read_tdp or write_tdp:
        MSR_RAPL_POWER_UNIT = msr.read(MSR_RAPL_POWER_UNIT_ADDR)
        units = parse_MSR_RAPL_POWER_UNIT(MSR_RAPL_POWER_UNIT)

        MSR_PKG_POWER_LIMIT = msr.read(MSR_PKG_POWER_LIMIT_ADDR)
        power_limits = parse_MSR_PKG_POWER_LIMIT(MSR_PKG_POWER_LIMIT, units)

        if read_tdp:
            print(dumps(power_limits, indent=4, cls=NamespaceEncoder))

        else:
            apply_delta(args.write_tdp, power_limits)
            result = build_MSR_PKG_POWER_LIMIT(power_limits, units)
            msr.write(MSR_PKG_POWER_LIMIT_ADDR, result)

            power_limits = parse_MSR_PKG_POWER_LIMIT(msr.read(MSR_PKG_POWER_LIMIT_ADDR), units)
            print(dumps(power_limits, indent=4, cls=NamespaceEncoder))

    if voltage_plane is not None:
        if voltage_value is None:
            prompt = build_MSR_VOLTAGE(SimpleNamespace(plane=voltage_plane, voltage=None))
            msr.write(MSR_VOLTAGE_ADDR, prompt)
            MSR_VOLTAGE = msr.read(MSR_VOLTAGE_ADDR)
            print(parse_MSR_UNDERVOLTAGE(MSR_VOLTAGE))
        else:
            prompt = build_MSR_VOLTAGE(SimpleNamespace(plane=voltage_plane, voltage=voltage_value))
            msr.write(MSR_VOLTAGE_ADDR, prompt)
            # Read back result
            prompt = build_MSR_VOLTAGE(SimpleNamespace(plane=voltage_plane, voltage=None))
            msr.write(MSR_VOLTAGE_ADDR, prompt)
            MSR_VOLTAGE = msr.read(MSR_VOLTAGE_ADDR)
            print(parse_MSR_UNDERVOLTAGE(MSR_VOLTAGE))


if __name__ == "__main__":
    main()
