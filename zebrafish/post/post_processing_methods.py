import numpy as np
import cv2
import logging

class DataConverter(object):

    def __init__(self):
        self._available_converters = [
            'pixel_diff_to_pixel_velocity',
            'pixel_to_cm',
            'rel_angle_rad_to_sin_rel_angle',
            'rel_angle_rad_to_cos_rel_angle'
        ]
        self.selected = {
            'pixel_diff_to_pixel_velocity':False,
            'pixel_to_cm':False,
            'rel_angle_rad_to_sin_rel_angle':False,
            'rel_angle_rad_to_cos_rel_angle':False
        }
        self.fps = 30.0
        self.pixel_to_cm_ratio = 1.0

    def run(self, data):
        if self.selected['pixel_diff_to_pixel_velocity']:
            logging.info('Converting pixel diff to pixel velocity, fps: ' + str(self.fps))
            data['velocity_pixel_x'] = data['pos_diff_x'] * self.fps / data['frame_diff']
            data['velocity_pixel_y'] = data['pos_diff_y'] * self.fps / data['frame_diff']
            data['velocity_pixel'] = data['pos_dist'] * self.fps / data['frame_diff']
            logging.info('Converted pixel diff to pixel velocity')
        if self.selected['pixel_to_cm']:
            logging.info('Converting pixel to cm, pixel_to_cm_ratio: ' + str(self.pixel_to_cm_ratio))
            try:
                data['velocity_cm'] = data['velocity_pixel'] * self.pixel_to_cm_ratio
                logging.info('Converted pixel_diff_to_pixel_velocity')
            except:
                logging.info('velocity_cm column does not exist. passing...')
        if self.selected['rel_angle_rad_to_sin_rel_angle']:
            logging.info('Converting rel_angle rad to sin rel_angle')
            data['sin_rel_angle'] = np.sin(data['rel_angle_rad'])
        if self.selected['rel_angle_deg_to_cos_rel_angle']:
            logging.info('Converting rel_angle rad to cos rel_angle')
            data['cos_rel_angle'] = np.cos(data['rel_angle_rad'])
        return data

class PositionBounder(object):
    """
    Filters position by xy coordinate(pixel) bounds.
    """
    def __init__(self):
        self.bounds = []

    def run(self, data):
        for i in range(len(self.bounds)):
            x_lower = self.bounds[i][0][0]
            x_upper = self.bounds[i][0][1]
            y_lower = self.bounds[i][1][0]
            y_upper = self.bounds[i][1][1]
            x_idx_lower = data['pos_x_in_frame'] > x_lower
            x_idx_upper = data['pos_x_in_frame'] < x_upper
            y_idx_lower = data['pos_y_in_frame'] > y_lower
            y_idx_upper = data['pos_y_in_frame'] < y_upper
            data['bound_{}-'.format(i) + str(self.bounds[i])] = x_idx_lower & x_idx_upper & y_idx_lower & y_idx_upper
        return data
