# Infinite Flight Autopilot

My first big project created on python

Console based program
## HOW TO USE IT:
__default__:
It run take-off and vnav function to set take-off power and climb, if stepclimb waypoints are insert in the FPL they will be execute.
### on launch
it search for a device, after it has found one, itrequest a FLEX temp

FLEX temp:
(based on Simbrief Take-off data)
- can give number like 0, 1, 2 to derate the take-off power (100%, 90%, 80%)
- can give FLEX temp (Airbus) for direct calucation (not real data used)
- can give DTO-SEL TEMP (Boeing) for a somewhat direct calc

Then it wait until aircraft is on runway and n1% is > 50% (about 30%-40% Throttle) <br> 
P.S. [It doesn't set if throttle is modified when reach 50% n1]

when you took off it automatically retract gear, and change speed to target (based on simbrief climb-profile)
for automatic climb, need to activate ALT and VS (not recomended if ATC is online)

at FL100 it turn off LandingLight and SeatBelt sign

# Project:

## Main.py
The main file to run for main usage, can be personalized.

## module
folder where there are all the functions and classes used to create the main.py



