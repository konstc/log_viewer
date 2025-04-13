# Log Viewer

## About

Log Viewer - easy to use Qt-powered application for browsing .csv files or any [cantools](https://cantools.readthedocs.io/)-supported J1939 logs (.log/.asc/.blf/.csv).

Features:
- Intuitive user interface. There is no need to write any code just to see the log.
- Multiple plot modes (merged plot / separated / manual).
- Plotting of spectras, cursor measurements, MIN/MAX/RMS calculations, etc.

![plot2](./resource/screenshots/plot2.png "Main window & spectrum")
![plot1](./resource/screenshots/plot1.png "Plotting phase currents")

## How to run/build

To make launching/building/testing/etc easier, shell scripts for Windows/Linux have been added, located in `scripts`.

To simply launch the application, you must have Python 3.9+ installed. Call `run.bat`/`run.sh` from the project root. For example:

```bat
scripts\win\run.bat
```

```bash
$ ./scripts/linux/run.sh
```

The script will create a virtual environment, if necessary (at the first launch).

If you need to build an executable file, you can do this using [pyinstaller](https://pyinstaller.org/). To do this, use `build_dist.bat`/`build_dist.sh` scripts in the same way as `run.bat`/`run.sh`. After running the script, the builded artifacts will be located in the `dist` directory.

Please note that after creating the executable file on the Windows platform, an application archive is created using [7-Zip](https://www.7-zip.org/). Install it first.
