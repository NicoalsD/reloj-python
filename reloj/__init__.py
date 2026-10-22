"""Reloj en Python: a terminal clock written without any library.

The package is split in layers that only depend on the ones below:

    core      pure logic (time, dates, time zones, math, Spanish texts)
    features  stateful tools (alarm, stopwatch, pomodoro, countdown...)
    ui        everything that draws on the terminal
    app       wires the layers together and runs the loop
"""
