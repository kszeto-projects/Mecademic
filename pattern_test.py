import numpy as np
import math

# calculate row and column position based on pattern and index

# def spiral_pattern(num_rows, num_cols):
#     # Calculate the layer of the spiral

#     spiral_index = np.zeros((num_rows*num_cols, 2))
    

    
#     return spiral_index

def diagonal_pattern(index, num_rows, num_cols):
    num_diag = (num_rows - 1) + (num_cols - 1) + 1
    d = np.arange(num_diag)

    # Calculate the number of elements in each diagonal
    diag_counts = np.minimum(d + 1, np.minimum(num_rows, num_cols))
    diag_counts[d >= np.maximum(num_rows, num_cols)] = np.minimum(num_rows, num_cols) - (d[d >= np.maximum(num_rows, num_cols)] - (np.maximum(num_rows, num_cols) - 1))
    
    # Find which diagonal the index falls into
    diag_index = np.searchsorted(np.cumsum(diag_counts), index, side='right')
    
    # Calculate the position within the diagonal
    pos_in_diag = index - (np.cumsum(diag_counts)[diag_index - 1] if diag_index > 0 else 0)
    
    
    # Calculate row and column based on the diagonal index and position
    if diag_index % 2 == 0:
        if diag_index >= np.minimum(num_rows, num_cols):
            col = diag_index - np.minimum(num_rows, num_cols) + pos_in_diag + 1
            row = diag_index - col
        else:
            row = diag_index - pos_in_diag
            col = pos_in_diag
    else:
        if diag_index >= np.maximum(num_rows, num_cols):
            row = diag_index - np.maximum(num_rows, num_cols) + pos_in_diag + 1
            col = diag_index - row
        else:
            row = pos_in_diag
            col = diag_index - pos_in_diag

    print(f'Index: {index}, Row: {row}, Column: {col}, Diagonal Index: {diag_index}, Position in Diagonal: {pos_in_diag}')
    
    return row, col

num_rows = 8
num_cols = 12

for index in range(num_rows * num_cols):
    row, col = spiral_pattern(index, num_rows, num_cols)
    print(f"Index: {index}, Row: {row}, Column: {col}")