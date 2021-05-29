"""
    SORT: A Simple, Online and Realtime Tracker
    Copyright (C) 2016-2020 Alex Bewley alex@bewley.ai

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import print_function

import os
import numpy as np
import glob
import time
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from scipy.spatial import distance_matrix
from lapsolver import solve_dense

class KalmanTracker(object):
    """
    This class represents the internal state of individual tracked objects observed as position.
    """
    def __init__(self, initial_position, tracker_id):
        """
        Initialises a tracker using initial position.
        """
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        #constant velocity model
        self.kf.F = np.array([[1,0,1,0],
                              [0,1,0,1],
                              [0,0,1,0],
                              [0,0,0,1]])
        self.kf.H = np.array([[1,0,0,0],
                              [0,1,0,0]])

        self.kf.R *= 1.
        self.kf.P[2:,2:] *= 1000. #give high uncertainty to the unobservable initial velocities
        self.kf.Q = Q_discrete_white_noise(dim=4, dt=1.0, var=0.01)

        self.kf.x[:2] = initial_position.reshape(2,1)
        self.time_since_update = 0
        self.id = tracker_id
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.nb_kf_pred = 0

    def update(self, position):
        """
        Updates the state vector with observed bbox.
        """
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(position)

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        self.kf.predict()
        self.nb_kf_pred += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self.kf.x[:2].reshape(-1))
        return self.history[-1]

    @property
    def state(self):
        return self.kf.x

    @property
    def position(self):
        return self.kf.x[:2]

    @property
    def velocity(self):
        return self.kf.x[2:4]


class MultiObjectKalmanTracker(object):
    def __init__(self, max_age=1, min_hits=3, distance_threshold=50.0):
        """
        Sets key parameters for SORT
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.trackers = []
        self.frame_count = 0
        self.new_id = 0
        self.distance_threshold = distance_threshold

    def initialize(self):
        self.trackers = []
        self.frame_count = 0
        self.new_id = 0

    def match_detections(self, detection_positions, tracker_positions):
        """
        Assigns detections to tracked object (both represented as positions)

        Returns 3 lists of matches, unmatched_detections and unmatched_trackers
        """
        matches = []
        unmatched_detections = []
        unmatched_trackers = []

        if(len(tracker_positions)==0):
            unmatched_detections = np.arange(len(detection_positions))
            return matches, unmatched_detections, unmatched_trackers

        dist = distance_matrix(tracker_positions, detection_positions)
        trk_rows, det_cols = solve_dense(dist)

        #distance threshold
        solved_dist = np.array([dist[trk_rows[i], det_cols[i]] for i in range(len(trk_rows))])
        solved_dist_bool = solved_dist < self.distance_threshold
        trk_rows_sel = trk_rows[solved_dist_bool]
        det_cols_sel = det_cols[solved_dist_bool]

        matches = np.concatenate([det_cols_sel.reshape(-1,1), trk_rows_sel.reshape(-1,1)], axis=1)
        unmatched_detections = np.array([i for i in range(len(detection_positions)) if i not in det_cols_sel])
        unmatched_trackers = np.array([i for i in range(len(tracker_positions)) if i not in trk_rows_sel])
        return matches, unmatched_detections, unmatched_trackers

    def update(self, dets):
        """
        Params:
          dets - a numpy array of detections in the format [[x1,y1,x2,y2],[x1,y1,x2,y2],...]
        Requires: this method must be called once for each frame even with empty detections (use np.empty((0, 5)) for frames without detections).
        Returns the a similar array, where the last column is the object ID.

        NOTE: The number of objects returned may differ from the number of detections provided.
        """
        self.frame_count += 1

        #ret: id, nb_kf_pred, filter state(position, velocity)
        ret = np.concatenate([dets, np.full((len(dets), 4), np.nan)], axis=-1)

        predicted_positions = [trk.predict() for trk in self.trackers]
        to_del = [i for i, pred_pos in enumerate(predicted_positions) if np.any(np.isnan(pred_pos))]
        for t in reversed(to_del):
            self.trackers.pop(t)
            predicted_positions.pop(t)
        predicted_positions = np.array(predicted_positions)
        matched, unmatched_dets, unmatched_trks = self.match_detections(dets, predicted_positions)

        #print(matched, unmatched_dets, unmatched_trks)
        # update matched trackers with assigned detections
        for m in matched:
            self.trackers[m[1]].update(dets[m[0], :])
            if self.trackers[m[1]].hit_streak >= self.min_hits:
                #ret[m[0], -1] = self.trackers[m[1]].id + 1 # +1 as MOT benchmark requires positive
                ret[m[0], 0] = self.trackers[m[1]].id
                ret[m[0], 1] = self.trackers[m[1]].nb_kf_pred
                ret[m[0], 2:] = self.trackers[m[1]].state.reshape(-1)


        # create and initialise new trackers for unmatched detections
        for i in unmatched_dets:
            trk = KalmanTracker(dets[i,:], self.new_id)
            self.new_id += 1
            self.trackers.append(trk)
            if trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits:
                #ret[i, -1] = trk.id + 1 # +1 as MOT benchmark requires positive
                ret[i, 0] = trk.id
                ret[i, 1] = trk.nb_kf_pred
                ret[i, 2:] = trk.state.reshape(-1)

        for i, trk in reversed(list(enumerate(self.trackers))):
            # remove dead tracklet
            if(trk.time_since_update > self.max_age):
                self.trackers.pop(i)

        return ret
