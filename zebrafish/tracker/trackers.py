import numpy as np
import logging
from tqdm import tqdm
import pandas as pd
from scipy.spatial import distance_matrix
from lapsolver import solve_dense

from .mokt import MultiObjectKalmanTracker

class Tracker(object):

    def __init__(self):
        self.new_col_names = ['id',
                              'found_after',
                              'is_new_id',
                              'frame_diff',
                              'pos_diff_x',
                              'pos_diff_y',
                              'pos_dist',
                              'rel_angle_deg_diff']
        self.position_names = ['pos_x_in_frame', 'pos_y_in_frame']
        self.angle_names = ['rel_angle_deg']
        self.bbox_names = ['bbox_tl_x_in_crop', 'bbox_tl_y_in_crop',
                           'bbox_br_x_in_crop', 'bbox_br_y_in_crop']

    def get_frame_idx(self, data):
        frame_num = data['frame_num'].iloc[0]
        frame_idx = [0]
        for i, fn in enumerate(data['frame_num']):
            if fn != frame_num:
                frame_idx.append(i)
                frame_num = fn
        frame_idx.append(len(data['frame_num']))
        return frame_idx

    def get_track_data(self, data):
        data_sorted = data.sort_values(by=['id', 'frame_num'])

        #found after
        if not 'found_after' in data_sorted.columns:
            found_after = np.full_like(data_sorted['id'], True, dtype=np.bool)
            curr_id = data_sorted['id'].iloc[0]
            for i, data_id in enumerate(data_sorted['id']):
                if data_id != curr_id:
                    found_after[i - 1] = False
                    curr_id = data_id
            data_sorted['found_after'] = found_after

        #is new id
        is_new_id = np.full_like(data_sorted['id'], False, dtype=np.bool)
        curr_id = data_sorted['id'].iloc[0]
        is_new_id[0] = True
        for i, data_id in enumerate(data_sorted['id']):
            if data_id != curr_id:
                is_new_id[i] = True
                curr_id = data_id
        data_sorted['is_new_id'] = is_new_id

        #frame diff
        tracked_frame = np.array(data_sorted['frame_num'])

        frame_diff_with_nan = np.full_like(data_sorted['frame_num'], np.nan, dtype=np.float)
        frame_diff_with_nan[1:] = tracked_frame[1:] - tracked_frame[:-1]

        frame_diff_with_nan[is_new_id] = np.nan
        data_sorted['frame_diff'] = frame_diff_with_nan

        #position diff
        tracked_position = np.array(data_sorted[self.position_names])

        position_diff_with_nan = np.full((len(tracked_position), 2), np.nan)
        position_diff_with_nan[1:] = tracked_position[1:] - tracked_position[:-1]

        position_diff_with_nan[is_new_id] = np.nan
        data_sorted['pos_diff_x'] = position_diff_with_nan[:, 0]
        data_sorted['pos_diff_y'] = position_diff_with_nan[:, 1]
        data_sorted['pos_dist'] = np.linalg.norm(position_diff_with_nan, axis=-1)

        #angle diff
        angles = np.array(data_sorted[self.angle_names[0]])
        angle_diff_with_nan = np.full_like(data_sorted[self.angle_names[0]], np.nan)
        angle_diff = angles[1:] - angles[:-1]
        angle_diff = np.where(angle_diff > 180.0, angle_diff - 360.0, angle_diff)
        angle_diff = np.where(angle_diff < -180.0, angle_diff + 360.0, angle_diff)

        angle_diff_with_nan[1:] = angle_diff
        angle_diff_with_nan[is_new_id] = np.nan
        data_sorted['rel_angle_deg_diff'] = angle_diff_with_nan

        data = data_sorted.sort_values(by=['frame_num', 'id'])
        return data

    def initialize(self):
        pass

    def get_id(self, data, start_frame_num, end_frame_num, frame_idx):
        pass

    def track(self, data, frame_cut=(0, None)):
        pass

class VicinityTracker(Tracker):

    def __init__(self,
                 nb_frames_to_find=15,
                 max_dist=25.0,
                 max_dist_inc_ratio=0.05):
        super(VicinityTracker, self).__init__()
        self.nb_frames_to_find = nb_frames_to_find
        self.max_dist = max_dist
        self.max_dist_inc_ratio = max_dist_inc_ratio
        self.new_id = 0

    def initialize(self):
        self.new_id = 0

    def get_id(self, data, start_frame_num, end_frame_num, frame_idx):
        #initialize columns
        new_col = np.full_like(data['frame_num'], np.nan, dtype=np.float)
        for name in self.new_col_names[:2]:
            data[name] = new_col

        #first frame
        current_frame_idx = frame_idx[start_frame_num]
        next_frame_idx = frame_idx[start_frame_num + 1]
        first_frame_ids = np.arange(next_frame_idx)

        self.new_id = first_frame_ids[-1] + 1
        data.loc[current_frame_idx:next_frame_idx - 1, 'id'] = first_frame_ids

        #track
        for current_frame in tqdm(range(start_frame_num + 1, end_frame_num)):
            current_data_idx_start = frame_idx[current_frame]
            current_data_idx_end = frame_idx[current_frame + 1] - 1
            current_data = data.loc[current_data_idx_start:current_data_idx_end]
            for i in range(1, self.nb_frames_to_find + 1):
                previous_frame_num = current_frame - i
                if previous_frame_num < start_frame_num:
                    break
                else:
                    not_found_idxs = np.isnan(np.array(current_data['id']))
                    if not_found_idxs.any():
                        previous_data_idx_start = frame_idx[previous_frame_num]
                        previous_data_idx_end = frame_idx[previous_frame_num + 1] - 1
                        previous_data = data.loc[previous_data_idx_start:previous_data_idx_end]
                        not_found_after_idxs = previous_data['found_after'] != 1
                        if not_found_after_idxs.any():
                            previous_pos = previous_data[self.position_names][not_found_after_idxs]
                            current_pos = current_data[self.position_names][not_found_idxs]
                            dist = distance_matrix(previous_pos, current_pos)
                            ####TODO: add angle dist
                            rows, cols = solve_dense(dist)
                            current_max_dist = self.max_dist + (1.0 + self.max_dist_inc_ratio * i)
                            for j in range(len(rows)):
                                if dist[rows[j], cols[j]] < current_max_dist:
                                    matching_previous_idx = previous_pos.index[rows[j]]
                                    matching_current_idx = current_pos.index[cols[j]]
                                    data.loc[matching_current_idx, 'id'] = previous_data.loc[matching_previous_idx, 'id']
                                    data.loc[matching_previous_idx, 'found_after'] = 1
                    else:
                        break
            for j in range(len(current_data)):
                current_data_idx = current_data_idx_start + j
                if np.isnan(data.loc[current_data_idx, 'id']):
                    data.loc[current_data_idx, 'id'] = self.new_id
                    self.new_id += 1
        return data

    def track(self, data, frame_cut=(0, None)):
        frame_idx = self.get_frame_idx(data)

        start_frame_num = frame_cut[0]
        end_frame_num = frame_cut[1]
        if end_frame_num == None:
            end_frame_num = len(frame_idx) - 1
        logging.info('Frame start: ' + str(start_frame_num) + ', Frame end: ' + str(end_frame_num))

        #track
        #id
        data = self.get_id(data, start_frame_num, end_frame_num, frame_idx)

        #data from tracking
        data = self.get_track_data(data)
        return data

class KalmanTracker(Tracker):

    def __init__(self,
                 max_age=15,
                 min_hits=0,
                 distance_threshold=50.0):
        super(KalmanTracker, self).__init__()
        self.mokt = MultiObjectKalmanTracker(max_age=max_age,
                                min_hits=min_hits,
                                distance_threshold=distance_threshold)

    def initialize(self):
        self.mokt.initialize()

    def get_id(self, data, start_frame_num, end_frame_num, frame_idx):
        tracked_result_list = []

        for current_frame in tqdm(range(start_frame_num, end_frame_num)):
            current_data_idx_start = frame_idx[current_frame]
            current_data_idx_end = frame_idx[current_frame + 1] - 1
            current_data = data.loc[current_data_idx_start:current_data_idx_end]
            current_bbox = np.array(current_data[self.position_names])
            tracked_result = self.mokt.update(current_bbox)
            tracked_result_list.append(tracked_result)

        tracked_result_concat = np.concatenate(tracked_result_list)
        data['id'] = tracked_result_concat[:, 0]
        data['nb_kf_pred'] = tracked_result_concat[:, 1]
        data['kf_pos_x'] = tracked_result_concat[:, 2]
        data['kf_pos_y'] = tracked_result_concat[:, 3]
        data['kf_vel_x'] = tracked_result_concat[:, 4]
        data['kf_vel_y'] = tracked_result_concat[:, 5]
        return data

    def track(self, data, frame_cut=(0, None)):
        frame_idx = self.get_frame_idx(data)

        start_frame_num = frame_cut[0]
        end_frame_num = frame_cut[1]
        if end_frame_num == None:
            end_frame_num = len(frame_idx) - 1
        logging.info('Frame start: ' + str(start_frame_num) + ', Frame end: ' + str(end_frame_num))

        #track
        #id
        data = self.get_id(data, start_frame_num, end_frame_num, frame_idx)

        #data from tracking
        data = self.get_track_data(data)
        return data
