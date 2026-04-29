"""
Demo program for Meca500 robot and Schunk gripper MEGP-25.
MCS500 place
"""

import mecademicpy.robot as mdr
import numpy as np
import threading
import time

from utils import *

meca500_ip = "192.168.0.100"
mcs500_ip = "192.168.0.101"
speed = 100
allow_change_speed = False

def do_until_input(mcs, meca, well_positions, mcs_func, meca_func, speed, pattern_id=0, prompt='Press Enter to stop the action...'):
    """
    Perform an action in a loop until the operator presses Enter.
    
    :param robot1: The first robot object (mcs).
    :param robot2: The second robot object (meca).
    :param well_positions: The grid of well positions.
    :param action_func: A function that performs the action (e.g., moving the robot).
    :param pattern: parameter to specify the pattern of movement (e.g., row-first, column-first, etc.)
    :param prompt: prompt to display to the user when waiting for input.
    """
    stop_event = threading.Event()
    
    def input_thread():
        wait_for_input(prompt)
        stop_event.set()
    
    def mcs_thread():
        start_robot(mcs, speed=speed)  # Ensure the robot is started before moving
        start_robot(meca, speed=speed)
        index = 0
          # Get the well positions once before starting the loop
        while not stop_event.is_set():
            row, col = patterns(pattern_id, index)
            mcs_func(mcs, well_positions, row, col)
            # rotary_occ = False
            # time.sleep(0.5)  # Small delay to avoid overwhelming the robot
            # while rotary_occ:
            #     time.sleep(0.1)  # Wait until the rotary is no longer occupied
            # rotary_occ = True
            mcs.MoveJump(*dispense_position)
            index += 1
            index = index % (num_rows * num_cols)

    def meca_thread():
        while not stop_event.is_set():
            # while rotary_occ:
            #     time.sleep(0.1)  # Wait until the rotary is no longer occupied
            # rotary_occ = True
            meca_func(meca)
            # rotary_occ = False  # Free up the rotary for the next cycle
            # print(f'Rotary state: {rotary_occ}')
            meca.WaitIdle(60)
    
    # Start both threads
    t1 = threading.Thread(target=input_thread)
    t2 = threading.Thread(target=mcs_thread)
    t3 = threading.Thread(target=meca_thread)
    t1.start()
    t2.start()
    t3.start()
    t1.join()  # Wait for input thread to finish
    t2.join()
    t3.join()

if __name__ == "__main__":
    meca500 = mdr.Robot()
    meca500.Connect(address=meca500_ip, disconnect_on_exception=False)
    print(f'Connected to {meca500.GetRobotInfo().model} at {meca500.GetRobotInfo().ip_address}')
    mcs500 = mdr.Robot()
    mcs500.Connect(address=mcs500_ip, disconnect_on_exception=False)
    print(f'Connected to {mcs500.GetRobotInfo().model} at {mcs500.GetRobotInfo().ip_address}')
    if allow_change_speed:
        speed = int(input('Enter robot speed (1-100, default 25): ') or 25)
    else:
        speed = 100

    # print(f'\nOperating Speed: {speed}')
    
    try:
        start_robot(meca500, speed=speed)
        start_robot(mcs500, speed=speed)
    except Exception as e:
        print(f'Error starting robots: {e}')
        meca500.Disconnect()
        mcs500.Disconnect()
        exit(1)

    while True:
        time.sleep(1)
        well_positions = palletize_any_angle(mcs500)
        dispense_position = teach_point(mcs500, 'dispense position')
        dispense_position[3] += 10
        pattern = int(input('0: column-first pattern \n1: row-first pattern \n2: zig-zag diagonal pattern \n3: snaking pattern \nPress Enter to start...\n') or 0)
        do_until_input(mcs500, meca500, well_positions, move_to_well_pos, pick_place_vial, speed=speed, pattern_id=pattern)

    print('Now disconnected from the robot.')