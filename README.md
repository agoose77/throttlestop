# throttlestop
Simple tool to manage thermal behaviour on Linux

Install tool with 
`sudo pip install git+https://github.com/agoose77/throttlestop.git#egg=throttlestop`

Install service with 30 second interval using 
`sudo throttlestop-install-service 30`,
and configure the service using the interactive prompt:
```bash
/usr/bin/python3 -m throttlestop voltage '{"cache": -149, "cpu": -149}'
/usr/bin/python3 -m throttlestop tdp '{"first": {"power_limit": 30}}'
/usr/bin/python3 -m throttlestop # Hit return to exit
Finished configuring service!
```

Activate service with
```bash
systemctl daemon-reload
systemctl enable throttlestop
systemctl start throttlestop
systemctl enable throttlestop.timer
systemctl start throttlestop.timer
```

Inspired by:
* https://github.com/mihic/linux-intel-undervolt
* https://gist.github.com/Mnkai/5a8edd34bd949199224b33bd90b8c3d4
* https://github.com/razvanlupusoru/Intel-RAPL-via-Sysfs/blob/master/README.txt#L112 (Though the scheme is incorrect)
* https://github.com/georgewhewell/undervolt
