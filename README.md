# Mecademic
Olympus Controls Mecademic Projects

## Install Mecademic Python API
`pip install mecademicpy`

For more examples and detailed usage of Robot class, see [MecademicPy GitHub](https://github.com/Mecademic/mecademicpy)

## DMEMS MCS500 Demo
### Overview
This project is used as a demo for Olympus Controls + Mecademic, and requires a direct network connection to the robot. No additional peripherals, sensors, grippers, or safety functionality is included in this project example. Basic wiring following the [safety installation guide](https://resources.mecademic.com/en/doc/MC-UM-MCS500/latest/manual/safety.html) should be sufficient. A pdf of the manual is provided in the files.

1. Run `DMEMS_2026_Mcs500_Demo.py`.
2. Teach point A1 and A12 following prompts.
3. Choose pattern to iterate through well positions.
4. Press Enter to pause and reteach points.

### Diagonal Zig-Zag
The diagonal pattern was a substantial amount of thinking and effort. I will do my best to describe the algorithm's approach and how it is implemented in the program. 

The goal is to return the row and column index given a single iterator index since we can also easily return the row and column index from a single iterator when traversing row-first or column-first; e.g.:
```[python]
def pattern(index):
  # function
  return row,col
```

#### 1. Calculate Diagonal Counts:


