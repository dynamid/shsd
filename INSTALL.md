# How to install and use SHSD

SHSD is not yet packaged and should be considered in very early alpha stage. Still, if you want to try it, here are some guideline on how to install it.

# Architecture

SHSD is architecured with a core and workers. All parts share a common configuration file `shsd.conf`.

The core (in `core` subdirectory) is responsible for data storage (sqlite), API access and web user interface. It uses Python3 and the Flask framework.

Workers (in `workers` subdirectory) are responsible for system monitoring: they analyse logs and report to the core. Currently, there are 2 workers :

* `loggers/dovecot-imap.py` which reads a dovecot log
* `devices/arpdevices.py` which reads the ARP table for neighboring devices

# Prerequisites

SHSD is developed and tested on Debian Strech (current stable). In order to use it, you need the following packages: python3-flask, python3-flask-sqlalchemy, python3-geojson, python3-geoip, geoip-database-contrib (+ the ones I forgot ;-) )

# Usage

You need to put the example config in `/etc/shsd.conf` or  ̀$HOME/.config/shsd.conf` (alternatively, there is a `-c` option in every script to specify a custom location).

To run the core, you can either `python3 shsd.py` or use WSGI with the example script provided in `doc`.

Then, you need to run a worker to feed the core. The currently only used worker is the dovecot parser, which you should run with permissions to access your mail.log : `python3 imap-dovecot.py`. This script can be launched periodically with cron

Then you should be able to point a web browser to the core (`http://localhost:5000` if you run it without WSGI on localhost, for instance) and "see" your IMAP logs.
