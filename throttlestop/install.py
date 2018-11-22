from pathlib import Path

service_script = """
[Unit]
Description=throttlestop

[Service]
Type=oneshot
ExecStart=throttlestop voltage '{"cache": -149, "cpu": -149}';throttlestop tdp '{"first": {"power_limit": 30}}';
"""


timer_script = """
[Unit]
Description=Apply throttlestop settings

[Timer]
Unit=throttlestop.service
# Wait 2 minutes after boot before first applying
OnBootSec=2min
# Run every 30 seconds
OnUnitActiveSec=30

[Install]
WantedBy=multi-user.target
"""


def main():
    target = Path("/etc/systemd/system/throttlestop.timer")
    target.write_text(timer_script)

    service = Path("/etc/systemd/system/throttlestop.service")
    service.write_text(service_script)
