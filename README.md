# throttlestop
Simple tool to manage thermal behaviour on Linux for Intel CPUs with a MSR. 

## Disclaimer
If this tool works, _great_! However, no guarantees are made that it won't hasten the heat death of the universe through the spontaneous combustion of your CPU.

![XKCD existential bug reports](https://imgs.xkcd.com/comics/existential_bug_reports.png)

## Installation
Requires `msr-tools`:
`sudo apt install msr-tools`

Install tool with 
`sudo pip install git+https://github.com/agoose77/throttlestop.git#egg=throttlestop`

Install service with 30 second interval and 4 minute delay using 
`sudo throttlestop-install-service -i 30s -d 4min`,
and configure the service using the interactive prompt (it will find the python binary with `sys.executable`):
```bash
Enter systemd configuration lines:
/usr/bin/python3 -m throttlestop voltage "{\"cache\": -149, \"cpu\": -149}"
/usr/bin/python3 -m throttlestop temperature "{\"offset\": 20}"
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

## API
`throttlestop SECTION [JSON-STRING]`,

where `SECTION` is one of (`tdp`, `voltage`, `temperature`). Provide JSON `JSON-STRING` argument to set the `SECTION` value, or omit it to read (as a JSON string).

Inspired by:
* https://github.com/mihic/linux-intel-undervolt
* https://gist.github.com/Mnkai/5a8edd34bd949199224b33bd90b8c3d4
* https://github.com/razvanlupusoru/Intel-RAPL-via-Sysfs/blob/master/README.txt#L112 (Though the scheme is incorrect)
* https://github.com/georgewhewell/undervolt
