import numpy as np

def convert_angle(angle, zero_angle='left'):
    """angle rad -> angle relative to flow"""
    if zero_angle == 'left':
        transform_rad = -np.sign(angle) * np.pi
        angle_rad = transform_rad + angle
    elif zero_angle == 'right':
        angle_rad = -yaw
    else:
        #temporary
        angle_rad = -yaw

    angle_deg = angle_rad * 180.0 / np.pi
    return angle_rad, angle_deg
