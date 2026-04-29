import mecademicpy.robot as mdr
import numpy as np
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
    if point_name == 'dispense position':
        curr_pos = robot.GetPose()
        print(f'Current position: {curr_pos}')
        curr_pos[2] += 10  # Move up by 10mm for picking
        print(f'Updated height for picking: {curr_pos}')
        robot.ActivateRobot()
        robot.MovePose(*curr_pos)
        robot.WaitIdle(60)
        robot.DeactivateRobot()
    wait_for_input(f'Set the robot to the {point_name} and press Enter...')
    robot.ActivateRobot()
    point = robot.GetPose()
    print(f'{point_name} set to: {point}')
    robot.DeactivateRobot()
    return point

def start_robot(robot, speed=25):
    print(f'Robot: {robot.GetRobotInfo().model} \nOperating Speed: {speed}')
    robot.ResetError()
    robot.SetJointVel(speed)
    robot.SetJointAcc(speed)
    robot.SetCartAcc(6*speed)
    if robot.GetRobotInfo().num_joints == 4:
        robot.ActivateRobot()
        robot.SetCartAngVel(speed*(50))
        robot.SetCartLinVel(speed*(50))
        robot.SetMoveJumpApproachVel(0,0,0,0)
        robot.SetConf(-1)
    elif robot.GetRobotInfo().num_joints == 6:
        robot.ActivateAndHome()
        robot.SetCartAngVel(speed*(10))
        # robot.setCartLinVel(25*50)

def palletize_any_angle(robot):
    """Improved palletizing function that allows for any angle of the well plate."""
    # prepare robot for moving by hand to teach points
    start_pos = [0, 0, -102, 0]
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

def move_to_well_pos(robot, well_positions, well_row, well_col):
    """Move the robot to a specific well position."""

    #appr_dist = 20 # change how much spindle moves up and down.
    #row = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'][well_row]
    well_position = well_positions[well_row, well_col]
    # print(f'Moving to well ({row}, {well_col+1}) at position: {well_position}')
    robot.MoveJump(*well_position)
    robot.WaitIdle(60)

def pick_place_vial(robot):
    """Move the robot to the pick position and simulate picking a vial."""
    low_speed = 25
    high_speed = 100
    robot.SetBlending(0)
    robot.MovePose(168.75, -102.274075, 80, -180, 0, -150)
    robot.SetJointVel(low_speed)
    robot.MoveLin(168.75, -102.274075, 58, -180, 0, -150)
    time.sleep(0.2)  # Simulate time taken to pick the vial
    robot.MoveLin(168.75, -102.274075, 90, -180, 0, -150)
    robot.MovePose(180, 0, 100, 180, 0, 120)
    robot.SetBlending(100)
    robot.SetJointVel(int(high_speed*1.5))
    for i in range(3):
        robot.MovePose(180, 0, 100, 180, 10, 120)
        robot.MovePose(180, 0, 100, -170, 0, 120)
        robot.MovePose(180, 0, 100, 180, -10, 120)
        robot.MovePose(180, 0, 100, -190, 0, 120)
    robot.MovePose(180, 0, 100, 180, 0, 120)

    robot.SetBlending(0)
    robot.SetJointVel(low_speed)
    robot.MovePose(137.25, 122.108989, 90, 180, 0, 120)
    robot.MoveLin(137.25, 122.108989, 60, 180, 0, 120)
    time.sleep(0.2)  # Simulate time taken to dispense the vial
    robot.SetBlending(100)
    robot.SetJointVel(int(high_speed*1.5))
    robot.MoveLin(137.25, 122.108989, 80, 180, 0, 120)
