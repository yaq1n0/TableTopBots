# Toy Robot Simulator

## Overview

Create an application in Python that will take in commands and output an end state.

We use this test as an indication of the kind of code that a candidate would write on a day-to-day basis. Please submit representative production-grade code with appropriate testing. Consider how the user will interact with the software.

## Description

The application is a simulation of a toy robot moving on a square tabletop, with the following characteristics:

- Dimensions: 5 units x 5 units
- No other obstructions on the table surface
- The robot is free to roam, but must be prevented from falling off
- Any movement that would result in the robot falling must be prevented, but further valid movement commands must still be allowed

## Commands

The application should support the following commands:

- `PLACE X,Y,F` - Put the robot on the table at position (X,Y) facing NORTH, SOUTH, EAST, or WEST
- `MOVE` - Move the robot one unit forward in the direction it is currently facing
- `LEFT` - Rotate the robot 90 degrees left without changing position
- `RIGHT` - Rotate the robot 90 degrees right without changing position
- `REPORT` - Announce the robot's current X, Y coordinates and facing direction

## Rules

- The origin (0,0) is the SOUTH WEST corner
- The first valid command must be a PLACE command
- After a valid PLACE, any sequence of commands may be issued in any order, including another PLACE
- All commands before the first valid PLACE are discarded
- A robot not on the table ignores MOVE, LEFT, RIGHT, and REPORT commands
- The robot must not fall off the table during movement or initial placement
- Any move that would cause the robot to fall is ignored
- Input can be from a file or standard input (developer's choice)

## Examples

### Example a)
```
PLACE 0,0,NORTH
MOVE
REPORT
```
Output: `0,1,NORTH`

### Example b)
```
PLACE 0,0,NORTH
LEFT
REPORT
```
Output: `0,0,WEST`

### Example c)
```
PLACE 1,2,EAST
MOVE
MOVE
LEFT
MOVE
REPORT
```
Output: `3,3,NORTH`

## Deliverables

- Production-grade Python application with appropriate testing
- Test data to exercise the application
- Host on GitHub or package as zip file