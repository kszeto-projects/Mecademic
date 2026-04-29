#!/usr/bin/env python3
"""
This is a well-plate dispensing/palletizing example showing how to use the mecademicpy API with a Mecademic robot.
This example connects to a robot at IP address 192.168.0.100, activates it, and loops through the well plate positions.
You can change the pattern of movement by changing the pattern_id parameter in the do_until_input function.
"""

import mecademicpy.robot as mdr
import numpy as np
import threading
import time

# Global Variables
spacing = 9  # Spacing between wells in mm
num_rows = 8
num_cols = 12
num_diag = num_rows + num_cols - 1
d = np.arange(num_diag)

# Calculate the number of elements in each diagonal
diag_counts = np.minimum(d + 1, np.minimum(num_rows, num_cols))
diag_counts[d >= np.maximum(num_rows, num_cols)] = np.minimum(num_rows, num_cols) - (d[d >= np.maximum(num_rows, num_cols)] - (np.maximum(num_rows, num_cols) - 1))

def wait_for_input(prompt='Press Enter to continue...'):
    """Wait for the user to press Enter."""
    input(prompt)

def teach_point(robot, point_name):
    wait_for_input(f'Set the robot to the {point_name} and press Enter...')
    robot.ActivateRobot()
    point = robot.GetPose()
    print(f'{point_name} set to: {point}')
    robot.DeactivateRobot()
    return point

def start_robot(robot,speed=20):
    """Start the robot by activating it."""
    # Do not need to home 4-axis SCARA
    robot.ResetError()
    robot.ActivateRobot()
    robot.SetJointVel(speed)
    robot.SetJointAcc(speed)
    robot.SetCartLinVel(speed*(50))
    robot.SetCartAngVel(speed*(50))
    robot.SetCartAcc(speed)
    robot.SetMoveJumpApproachVel(0,0,0,0)
    robot.SetConf(-1)

def palletize_any_angle(robot):
    """Improved palletizing function that allows for any angle of the well plate."""
    # prepare robot for moving by hand to teach points
    start_pos = [0, 0, -98.5, 0]
    robot.MoveJoints(*start_pos)
    print('Set reference frame for well plate by setting 2 points: origin and y-axis point.')
    robot.WaitIdle(60)
    robot.DeactivateRobot()

    # Example grid size for a 96-well plate (12 columns x 8 rows A-H)
    pallet_grid = np.zeros([num_rows, num_cols, 4])  # Initialize
    rows = np.arange(0, num_rows*spacing, spacing)  # 8 rows (A-H) spaced 9mm apart
    cols = np.arange(0, num_cols*spacing, spacing)  # 12 columns (1-12) spaced 9mm apart
    row,col = np.meshgrid(rows, cols, indexing='ij')  # Create a grid of row and column indices
    pos_grid = np.stack((row, col), axis=-1)  # Combine into a grid of positions

    # use y-axis (columns) to determine angle since it's longer and will provide better angle accuracy.
    origin = teach_point(robot, 'origin point')
    y_axis_point = teach_point(robot, 'last column point')

    # Calculate the angle of the y-axis based on the origin and y-axis point
    y_axis_vector = np.array(y_axis_point) - np.array(origin)
    y_axis_angle = np.arctan2(y_axis_vector[1], y_axis_vector[0])  # Angle in radians
    x_axis_angle = y_axis_angle - np.pi / 2  # Perpendicular to y-axis
    # print(f'Calculated x-axis angle: {np.degrees(x_axis_angle):.2f} degrees')
    print(f'Calculated y-axis angle: {np.degrees(y_axis_angle):.2f} degrees')
    
    T = np.array([[np.cos(x_axis_angle), -np.sin(x_axis_angle), origin[0]],
                  [np.sin(x_axis_angle),  np.cos(x_axis_angle), origin[1]],
                  [0, 0, 1]])  # Rotation
    
    pos_grid = pos_grid.reshape(-1, 2)  # Flatten the grid to (96, 2)
    pos_grid_homogeneous = np.hstack((pos_grid, np.ones((num_rows*num_cols, 1))))  # Convert to homogeneous coordinates
    transformed_positions = pos_grid_homogeneous @ T.T  # Apply transformation

    pos_grid = transformed_positions[:, :2].reshape(num_rows, num_cols, 2)  # Reshape back to grid format

    #print(pos_grid)  # Should be (96, 3) with x, y, and homogeneous coordinate

    pallet_grid[:, :, :2] = pos_grid[:, :, :2]  # x positions
    pallet_grid[:, :, 2] = 11.5  # z position (height of the wells)
    #print(pallet_grid)

    return pallet_grid

def move_to_well_pos(robot, well_positions, well_row, well_col):
    """Move the robot to a specific well position."""

    #appr_dist = 20 # change how much spindle moves up and down.
    #row = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'][well_row]
    well_position = well_positions[well_row, well_col]
    # print(f'Moving to well ({row}, {well_col+1}) at position: {well_position}')
    robot.MoveJump(*well_position)
    robot.WaitIdle(60)

def patterns(pattern_id, index):
    match pattern_id:
        case 0:  # column-first
            row = index % num_rows  # row cycling (A-H)
            col = (index // num_rows) % num_cols  # column cycling (1-12)
        case 1:  # row-first
            col = index % num_cols  # column cycling (1-12)
            row = (index // num_cols) % num_rows  # row cycling (A-H)
        case 2:  # zig-zag diagonally            
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
        case 3:  # snaking pattern
            row = (index // num_cols) % num_rows
            if (index // num_cols) % 2 == 0:
                col = index % num_cols
            else:
                col = num_cols - 1 - (index % num_cols)
        

    return row, col


def do_until_input(robot, well_positions, action_func, speed=25, pattern_id=0, prompt='Press Enter to stop the action...'):
    """
    Perform an action in a loop until the operator presses Enter.
    
    :param robot: The robot object.
    :param well_positions: The grid of well positions.
    :param action_func: A function that performs the action (e.g., moving the robot).
    :param pattern: parameter to specify the pattern of movement (e.g., row-first, column-first, etc.)
    :param prompt: prompt to display to the user when waiting for input.
    """
    stop_event = threading.Event()
    
    def input_thread():
        wait_for_input(prompt)
        stop_event.set()
    
    def action_thread():
        start_robot(robot, speed=int(speed))  # Ensure the robot is started before moving
        index = 0
          # Get the well positions once before starting the loop
        while not stop_event.is_set():
            row = index % 8  # row cycling (A-H)
            col = (index // 8) % 12  # column cycling (1-12)
            row, col = patterns(pattern_id, index)
            action_func(robot, well_positions, row, col)
            index += 1
            index = index % (num_rows * num_cols)
            time.sleep(0.1)  # Small delay to avoid overwhelming the robot
    
    # Start both threads
    t1 = threading.Thread(target=input_thread)
    t2 = threading.Thread(target=action_thread)
    t1.start()
    t2.start()
    t1.join()  # Wait for input thread to finish
    t2.join()  # Wait for action thread to finish

if __name__ == "__main__":
    with mdr.Robot() as robot:
        robot.Connect(address='192.168.0.101', disconnect_on_exception=False)
        speed = int(input('Enter robot speed (1-100, default 25): ') or 25)

        while(True):
            start_robot(robot, speed=speed)
            well_positions = palletize_any_angle(robot)
            #iterate_well_positions(robot)
            pattern = int(input('0: column-first pattern \n1: row-first pattern \n2: zig-zag diagonal pattern \n3: snaking pattern \nPress Enter to start...\n') or 0)
            do_until_input(robot, well_positions, move_to_well_pos, speed=speed, pattern_id=pattern, prompt="Press Enter to reset well positions...")
    print('Now disconnected from the robot.')