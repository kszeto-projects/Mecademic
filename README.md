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
The first step is to calculate the number of well positions in each diagonal. Let's denote the smaller row dimension as `m` and the larger column dimension as `n`. The count for the first diagonal starts at 1 and increases by one up to the `m`^th dimension. Then the diagonal counts stay the same until the `n`^th diagonal. It then decreases by 1 until the `(m+n-1)`th diagonal. For example, the diagonal counts for an 8x12 grid is: `[1,2,3,4,5,6,7,8,8,8,8,8,7,6,5,4,3,2,1]`


#### 2. Calculate Diagonal Index and Position:
Next we need to know which diagonal the index falls into, and which position in that diagonal. This gives us enough information to figure out the row and column indices. To calculate the diagonal index, we compute the cumulative sum of the counts:

`cumulative sum = [1,3,6,10,15,21,28,36,44,52,60,68,75,81,86,90,93,95,96]`

and find the diagonal based on the index. For example, if the index is 32, the diagonal index would be 7.

The position in the diagonal can be calculated by subtracting the cumulative sum of the previous diagonal index from the index. For example, if the index is 32 again, the diagonal index is 7 and the corresponding cumulative sum of the previous diagonal index is 28. The position in the diagonal would return `32 - 28 = 4`.

#### 3. Calculate Row and Column Index:
We can observe the pattern in the file, diagonal_zig_zag_template, and also confirm with the sample diagonal zig-zag python tool, to see that if the diagonal index is even, the column index follows the position value (up until the smaller row dimension). If the diagonal index is odd, the row index follows the position value until the diagonal index is greater than the larger column dimension.

This allows flexibility into the well plate dimensions rather than using a lookup table.