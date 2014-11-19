#!/usr/bin/env python

# iDumpster.py is the program that runs on the RPi located at the dumster end.
#
# Pi's running iDumpster.py have their GPIO connected to proximity sensors which
# help in sensing the trash level. This is reported to the RPi server, i.e.
# iDumpster_central.py using AMQP
