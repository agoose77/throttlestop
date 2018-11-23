from pathlib import Path
import sys

service_script = """
[Unit]
Description=throttlestop

[Service]
Type=oneshot
User=root
{exec_lines}

[Install]
WantedBy=multi-user.target
"""


timer_script = """
[Unit]
Description=Apply throttlestop settings

[Timer]
Unit=throttlestop.service
# Wait 2 minutes after boot before first applying
OnBootSec={delay}
# Run every {interval}
OnUnitActiveSec={interval}

[Install]
WantedBy=multi-user.target
"""


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-i", "--interval", default="30s", type=str)
    parser.add_argument("-d", "--delay", default="4min", type=str)
    args = parser.parse_args()
    lines = []

    line_prefix = f"{sys.executable} -m throttlestop "
    exec_line = "ExecStart={}"

    print("Enter systemd configuration lines:")

    while True:
        line = input(line_prefix)
        if not line:
            break

        lines.append(exec_line.format(line_prefix + line))

    target = Path("/etc/systemd/system/throttlestop.timer")
    target.write_text(timer_script.format(interval=args.interval, delay=args.delay))

    service = Path("/etc/systemd/system/throttlestop.service")
    service.write_text(service_script.format(exec_lines='\n'.join(lines)))

    print("Finished configuring service!")


if __name__ == "__main__":
    main()
