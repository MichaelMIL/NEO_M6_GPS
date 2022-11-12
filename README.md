# Project Title

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## About <a name = "about"></a>

Neo-6m GPS controller - with PUBX and UBX commands support.

## Getting Started <a name = "getting_started"></a>

Place GPS directory in the boards lib directory

## Usage <a name = "usage"></a>

```
from GPS import GPS_UART
import board
import busio

RX = board.GP5
TX = board.GP4

uart = busio.UART(TX, RX, baudrate=9600, timeout=3)
gps = GPS_UART(uart, debug=True)

gps.disable_nmea_output() # Disables periodic nmea serial output

while True:
    print(gps.read_gps_data()) # Send command for getting data and print

```
