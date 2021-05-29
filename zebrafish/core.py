import numpy as np
import logging
import cv2
import os
from moviepy.editor import VideoFileClip
import matplotlib.pyplot as plt
from tqdm import tqdm
import plotly.graph_objects as go
from PIL import Image
import pandas as pd
from glob import glob
import time

from zebrafish.detector import ThresholdDetector
from zebrafish.tracker import VicinityTracker, KalmanTracker
from zebrafish.post import DataConverter, PositionBounder
from zebrafish.saver import DetectionDataSaver, PostprocessDataSaver

from zebrafish.utils import convert_angle

class VideoProcessor(object):

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.overall_crop = np.array([[0,1290],[2120,3400]])
        self._video_path = None
        self.image_height = 2160
        self.image_width = 3840
        self.fps = 30.0
        self.frame_num = 0

    @property
    def video_path(self):
        return self._video_path

    @video_path.setter
    def video_path(self, path):
        self._video_path = path


class DetectionProcessor(VideoProcessor):

    def __init__(self, default_detector='ThresholdDetector'):
        super(DetectionProcessor, self).__init__()
        self.flow_left_to_right = True #water flow: left to right

        #text params (x:width, y:height)
        self.text_font_size = 1.0
        self.ang_text_y_diff = 50

        self._available_detectors = {
            'ThresholdDetector': ThresholdDetector()
        }
        self._detector_name = default_detector
        self._detector = self._available_detectors[self._detector_name]
        self.saver = DetectionDataSaver()

    def reset(self):
        self.saver.clear()
        self.frame_num = 0

    def save_detection_data(self, video_path):
        self.video_path = video_path
        clip = VideoFileClip(video_path)
        logging.info('Saving detection data...')

        #reset
        self.reset()

        for frame in clip.iter_frames(fps=self.fps, logger='bar'):
            cropped_img = frame[self.overall_crop[0,0]:self.overall_crop[1,0],
                            self.overall_crop[0,1]:self.overall_crop[1,1], :]

            position, angle, hulls, angle_vector = self._detector.detect_position_and_angle(cropped_img)
            if len(position) > 0:
                pos_x_in_crop = position[:, :1]
                pos_y_in_crop = position[:, 1:]
                pos_x_in_frame = pos_x_in_crop + self.overall_crop[0,1]
                pos_y_in_frame = pos_y_in_crop + self.overall_crop[0,0]

                if self.flow_left_to_right:
                    zero_angle = 'left'
                else:
                    zero_angle = 'right'
                rel_ang_rad, rel_ang_deg = convert_angle(angle, zero_angle=zero_angle)

                bboxes = self._detector.convert_hulls_to_bboxes(hulls)
                bbox_tl_x_in_crop = bboxes[:, :1]
                bbox_tl_y_in_crop = bboxes[:, 1:2]
                bbox_br_x_in_crop = bboxes[:, 2:3]
                bbox_br_y_in_crop = bboxes[:, 3:]

                angle = np.expand_dims(angle, axis=-1)
                rel_ang_rad = np.expand_dims(rel_ang_rad, axis=-1)
                rel_ang_deg = np.expand_dims(rel_ang_deg, axis=-1)
                data = np.concatenate([pos_x_in_crop,
                                       pos_y_in_crop,
                                       pos_x_in_frame,
                                       pos_y_in_frame,
                                       bbox_tl_x_in_crop,
                                       bbox_tl_y_in_crop,
                                       bbox_br_x_in_crop,
                                       bbox_br_y_in_crop,
                                       angle,
                                       angle_vector,
                                       rel_ang_rad,
                                       rel_ang_deg], axis=-1)
                self.saver.add_data_by_frame(data, self.frame_num)
            self.frame_num += 1

        #save data
        self.saver.save()
        clip.close()

    def get_detection_frame(self, frame):
        frame = np.copy(frame)
        cropped_img = frame[self.overall_crop[0,0]:self.overall_crop[1,0],
                            self.overall_crop[0,1]:self.overall_crop[1,1], :]
        #draw detection
        if self.flow_left_to_right:
            zero_angle = 'left'
        else:
            zero_angle = 'right'
        cropped_detection_img = self._detector.draw_detection_img(cropped_img, zero_angle=zero_angle)
        frame[self.overall_crop[0,0]:self.overall_crop[1,0],
              self.overall_crop[0,1]:self.overall_crop[1,1], :] = cropped_detection_img

        #draw crop
        cv2.rectangle(frame, (self.overall_crop[0, 1], self.overall_crop[0, 0]),
                      (self.overall_crop[1, 1], self.overall_crop[1, 0]), (255, 0, 0), 2)
        return frame

    def save_detection_video(self, video_path):
        names = video_path.split(os.path.sep)
        file_name = names[-1].split('.')[0] + '_detection.mp4'
        video_output_path_list = names[:-1] + ['detection_video', file_name]
        video_output_path = os.path.join(*video_output_path_list)
        clip = VideoFileClip(video_path)
        logging.info('Saving detection video...')
        out_clip = clip.fl(lambda gf, t: self.get_detection_frame(gf(t)), [])
        out_clip.write_videofile(video_output_path, audio=False, fps=self.fps)
        logging.info('Saved detection video at: ' + video_output_path)
        clip.close()

    def get_preview(self, video_path):
        clip = VideoFileClip(video_path)
        first_frame = clip.get_frame(0)
        step_images = [np.copy(first_frame)]
        step_names = ['first_frame', ]
        if self._detector_name == 'ThresholdDetector':
            detection_step_images, detection_step_names = self._detector.get_preview_images(first_frame, self.overall_crop)
            step_images += detection_step_images
            step_names += detection_step_names
        else:
            pass
        clip.close()
        return step_images, step_names

    @property
    def video_path(self):
        return self._video_path

    @video_path.setter
    def video_path(self, path):
        self._video_path = path
        self.saver.video_path = path

    @property
    def detector(self):
        return self._detector_name

    @detector.setter
    def detector(self, detector_name):
        self._detector_name = detector_name
        self._detector = self._available_detectors[detector_name]


class PostProcessor(VideoProcessor):

    def __init__(self, default_tracker='KalmanTracker'):
        super(PostProcessor, self).__init__()
        self.video_data = None
        self.frame_idx = None
        #draw pos ang params
        self.pos_draw_radius = 15
        #self.ang_draw_length = 25
        self.ang_draw_ratio = 2.0
        #draw text params (x:width, y:height)
        self.text_font_size = 1.0
        self.text_x_diff = 30
        self.text_start_y_diff = -50
        self.text_y_increment = 40


        self.ang_text_y_diff = 50
        self.id_text_y_diff = -50

        self._available_trackers = {
            'VicinityTracker': VicinityTracker(),
            'KalmanTracker': KalmanTracker(),
        }
        self._tracker_name = default_tracker
        self.run_tracker = True
        self._tracker = self._available_trackers[self._tracker_name]
        self._post_methods = {
            'DataConverter': DataConverter(),
            'PositionBounder': PositionBounder()
        }
        self._post_methods_selected = {
            'DataConverter': False,
            'PositionBounder': False
        }
        self.saver = PostprocessDataSaver()

        #video data
        self.video_data = None
        self.frame_idx = None
        self.detected_frames = None
        self.frame_idx_dict = None

    def get_frame_idx(self, data):
        frame_num = data['frame_num'].iloc[0]
        frame_idx = [0]
        for i, fn in enumerate(data['frame_num']):
            if fn != frame_num:
                frame_idx.append(i)
                frame_num = fn
        frame_idx.append(len(data['frame_num']))
        return frame_idx


    def set_video_data(self, data):
        data = data.sort_values(by=['frame_num', 'id'])
        self.video_data = data
        self.frame_idx = self.get_frame_idx(data)

        valid_frames = (np.array(self.video_data['frame_num'])[self.frame_idx[:-1]]).astype(np.int)
        last_frame = valid_frames[-1]
        self.detected_frames = np.full(last_frame + 1, False)
        self.detected_frames[valid_frames] = True

        self.frame_idx_dict = {vframe:(self.frame_idx[i], self.frame_idx[i+1])
                              for i, vframe in enumerate(valid_frames)}

    def save_post_data(self, post_data_path, frame_cut=(0, None)):
        self.post_data_path = post_data_path
        logging.info('Reading from: ' + post_data_path)
        try:
            data = pd.read_csv(post_data_path)
        except:
            data = pd.read_excel(post_data_path)
        if self.run_tracker:
            self._tracker.initialize()
            data = self._tracker.track(data, frame_cut=frame_cut)
        if self._post_methods_selected['PositionBounder']:
            data = self._post_methods['PositionBounder'].run(data)
        if self._post_methods_selected['DataConverter']:
            data = self._post_methods['DataConverter'].run(data)
        self.saver.save(data)
        logging.info('Post data saved.')
        return self.saver.output_file_path

    def draw_post_data(self, img, frame_num):
        idx_start = self.frame_idx_dict[frame_num][0]
        idx_end = self.frame_idx_dict[frame_num][1]
        #draw pos circle
        pos = np.array(self.video_data[['pos_x_in_crop', 'pos_y_in_crop']].iloc[idx_start:idx_end])
        pos_int = pos.astype(int)
        pos_int_list = [tuple(p) for p in pos_int]
        for i in range(len(pos_int_list)):
            cv2.circle(img, pos_int_list[i], self.pos_draw_radius, (0,255,0), thickness=2)

        #draw angle vector
        angle_vector = np.array(self.video_data[['angle_vector_x', 'angle_vector_y']].iloc[idx_start:idx_end])
        arrow_start_points = (pos - angle_vector).astype(np.int)
        arrow_end_points = (arrow_start_points + self.ang_draw_ratio * angle_vector).astype(np.int)
        start_point_list = [tuple(p) for p in arrow_start_points]
        end_point_list = [tuple(p) for p in arrow_end_points]
        for i in range(len(start_point_list)):
            cv2.arrowedLine(img, start_point_list[i], end_point_list[i],
                            (255, 0, 0), 1)

        ###text
        text_pos_int = np.copy(pos_int)
        text_pos_int[:, 0] += self.text_x_diff
        text_pos_int[:, 1] += self.text_start_y_diff
        text_pos_int_list = [tuple(p) for p in text_pos_int]

        #draw id text
        tracking_id = self.video_data['id'].iloc[idx_start:idx_end]
        for i in range(len(text_pos_int_list)):
            cv2.putText(img, 'ID: {}'.format(tracking_id.iloc[i]), text_pos_int_list[i],
                        cv2.FONT_HERSHEY_SIMPLEX, self.text_font_size, (0,0,255), 2)

        #draw pos text
        text_pos_int[:, 1] += self.text_y_increment
        text_pos_int_list = [tuple(p) for p in text_pos_int]
        for i in range(len(text_pos_int_list)):
            cv2.putText(img, 'pos:{:.1f}, {:.1f}'.format(pos[i, 0], pos[i, 1]), text_pos_int_list[i],
                        cv2.FONT_HERSHEY_SIMPLEX, self.text_font_size, (0,0,255), 2)

        #draw vel text
        vel = np.array(self.video_data[['velocity_pixel_x', 'velocity_pixel_y']].iloc[idx_start:idx_end])
        text_pos_int[:, 1] += self.text_y_increment
        text_pos_int_list = [tuple(p) for p in text_pos_int]
        for i in range(len(text_pos_int_list)):
            cv2.putText(img, 'vel:{:.1f}, {:.1f}'.format(vel[i, 0], vel[i, 1]), text_pos_int_list[i],
                        cv2.FONT_HERSHEY_SIMPLEX, self.text_font_size, (0,0,255), 2)

        #draw acc text
        acc = np.array(self.video_data[['acc_pixel_x', 'acc_pixel_y']].iloc[idx_start:idx_end])
        text_pos_int[:, 1] += self.text_y_increment
        text_pos_int_list = [tuple(p) for p in text_pos_int]
        for i in range(len(text_pos_int_list)):
            cv2.putText(img, 'acc:{:.1f}, {:.1f}'.format(acc[i, 0], acc[i, 1]), text_pos_int_list[i],
                        cv2.FONT_HERSHEY_SIMPLEX, self.text_font_size, (0,0,255), 2)

        #draw angle text
        ang = self.video_data['rel_angle_deg'].iloc[idx_start:idx_end]
        text_pos_int[:, 1] += self.text_y_increment
        text_pos_int_list = [tuple(p) for p in text_pos_int]
        for i in range(len(text_pos_int_list)):
            cv2.putText(img, 'ang: {:.1f}'.format(ang.iloc[i]), text_pos_int_list[i],
                        cv2.FONT_HERSHEY_SIMPLEX, self.text_font_size, (0,0,255), 2)
        return img

    def get_post_frame(self, frame, t):
        #new_frame = np.ones((self.image_height, self.image_width, 3))*255.0
        new_frame = np.zeros((self.image_height, self.image_width, 3))
        cropped_img = frame[self.overall_crop[0,0]:self.overall_crop[1,0],
                            self.overall_crop[0,1]:self.overall_crop[1,1], :]
        cropped_img_height = self.overall_crop[1,0] - self.overall_crop[0,0]
        cropped_img_width = self.overall_crop[1,1] - self.overall_crop[0,1]

        frame_num = int(t * self.fps)

        if frame_num < len(self.detected_frames):
            if self.detected_frames[frame_num]:
                cropped_img = self.draw_post_data(cropped_img, frame_num)

        new_frame[:cropped_img_height, :cropped_img_width, :] = cropped_img
        return new_frame

    def save_post_video(self, video_path, post_data_path):
        logging.info('Reading post data from: ' + post_data_path)
        try:
            data = pd.read_csv(post_data_path)
        except:
            data = pd.read_excel(post_data_path)

        self.set_video_data(data)

        logging.info('Reading video from: ' + video_path)
        path_names = post_data_path.split(os.path.sep)
        video_output_path_list = path_names[:-1] + ['post_video', path_names[-1].split('.')[0] + '.mp4']
        video_output_path = os.path.join(*video_output_path_list)
        clip = VideoFileClip(video_path)
        logging.info('Saving post video...')

        out_clip = clip.fl(lambda gf, t: self.get_post_frame(gf(t), t), [])
        out_clip.write_videofile(video_output_path, audio=False, fps=self.fps)
        logging.info('Saved post video at: ' + video_output_path)
        clip.close()

    @property
    def post_data_path(self):
        return self._post_data_path

    @post_data_path.setter
    def post_data_path(self, path):
        self._post_data_path = path
        self.saver.post_data_path = path

    @property
    def video_path(self):
        return self._video_path

    @video_path.setter
    def video_path(self, path):
        self._video_path = path

    @property
    def tracker(self):
        return self._tracker_name

    @tracker.setter
    def tracker(self, tracker_name):
        self._tracker_name = tracker_name
        self._tracker = self._available_trackers[tracker_name]

class Processor(object):

    def __init__(self):
        self.data_files_dir = 'data'
        self._detection_file_paths = []
        self._post_file_paths = {'data':[], 'video':[]}
        self._process_options = []
        self.detection_processor = DetectionProcessor()
        self.postprocessor = PostProcessor()
        self._detection_output_type_list = ['video', 'data', 'data+video']
        self._detection_output_type = 'data'
        self._post_output_type_list = ['video', 'data']
        self._post_output_type = 'data'
        self.preview_file_path = None

    def run_detection(self):
        logging.info('Running detection...')
        if len(self._detection_file_paths) == 0:
            logging.info('No files to run.')
        for p in self._detection_file_paths:
            file_name = p.split(os.path.sep)[-1]
            exten = p.split('.')[-1]
            logging.info('File:' + file_name)
            if self._detection_output_type == self._detection_output_type_list[0]:
                self.detection_processor.save_detection_video(p)
            elif self._detection_output_type == self._detection_output_type_list[1]:
                self.detection_processor.save_detection_data(p)
            else:
                self.detection_processor.save_detection_data(p)
                self.detection_processor.save_detection_video(p)

    def run_post(self):
        logging.info('Running post...')
        if self._post_output_type == self._post_output_type_list[1]:
            if len(self._post_file_paths['data']) == 0:
                logging.info('No files to run.')
            for p in self._post_file_paths['data']:
                logging.info('File to process:\ndata: {}'.format(p['data']))
                self.postprocessor.save_post_data(p['data'])
        else:
            if len(self._post_file_paths['video']) == 0:
                logging.info('No files to run.')
            for p in self._post_file_paths['video']:
                logging.info('File to process:\ndata: {} video: {}'.format(p['data'], p['video']))
                self.postprocessor.save_post_video(p['video'], p['data'])

    def plot_image(self, img, title, scale_factor=0.25):
        logging.info(title)
        source_img = Image.fromarray(img)
        img_width = img.shape[1]
        img_height = img.shape[0]
        x_axis_data = {
            'x': np.arange(int(img_width)),
            'y': np.zeros(int(img_width)),
            'type': 'scatter',
            'mode': 'markers',
            'marker': {'opacity': 0},
            'hoverinfo': 'x+y'
        }
        y_axis_data = {
            'x': np.zeros(int(img_height)),
            'y': np.arange(int(img_height)),
            'type': 'scatter',
            'mode': 'markers',
            'marker': {'opacity': 0},
            'hoverinfo': 'x+y'
        }
        data = [x_axis_data, y_axis_data]
        layout = go.Layout(
            title=go.layout.Title(
                text=title
            ),
            showlegend=False,
            hovermode='closest',
            xaxis = go.layout.XAxis(
                showgrid=False,
                range=[0, img_width],
                spikemode='across'
            ),
            yaxis = go.layout.YAxis(
                showgrid=False,
                autorange='reversed',
                range=[0, img_height],
                scaleanchor='x',
                scaleratio=1,
                spikemode='across'
            ),
            width = img_width * scale_factor,
            height = img_height * scale_factor,
            margin = {'l': 0, 'r': 0, 't': 0, 'b': 0},
            images = [
                go.layout.Image(
                    x=0,
                    y=0,
                    sizex=img_width,
                    sizey=img_height,
                    xref='x',
                    yref='y',
                    xanchor='left',
                    yanchor='top',
                    opacity=1.0,
                    layer='below',
                    source=source_img
                )
            ]
        )
        fig = go.Figure(data=data, layout=layout)
        #py.iplot(fig)
        fig.show()
        #return fig

    def preview_detection(self):
        if self.preview_file_path != None:
            step_imgs, step_names = self.detection_processor.get_preview(self.preview_file_path)
            for i in range(len(step_imgs)):
                self.plot_image(step_imgs[i], step_names[i], scale_factor=0.25)
        else:
            logging.info('No mp4 file to preview. Add mp4 file path first.')


    def update_file_paths(self):
        file_paths = sorted(glob(os.path.join(self.data_files_dir, '*.*')))
        detection_file_paths = []
        post_file_paths = {'data':[], 'video':[]}
        excluded_files = []
        for p in file_paths:
            file_name = p.split(os.path.sep)[-1]
            file_name_split = file_name.split('.')
            exten = file_name_split[-1]
            no_exten_file_name = file_name_split[-2]
            if exten == 'mp4' or exten == 'MP4':
                detection_file_paths.append(p)
            elif exten == 'csv' or exten == 'xlsx':
                no_exten_file_name_split = no_exten_file_name.split('_')
                suffix = no_exten_file_name_split[-1]
                path_dict = {'data':p}
                if suffix == 'detection':
                    post_file_paths['data'].append(path_dict)
                elif suffix == 'post':
                    video_file_name = '_'.join(no_exten_file_name_split[:-2])
                    paths = sorted(glob(os.path.join(self.data_files_dir,  video_file_name + '.*4')))
                    try:
                        path_dict = {'data':p}
                        path_dict['video'] = paths[0]
                        post_file_paths['video'].append(path_dict)
                    except:
                        logging.info('No video file name of ' + video_file_name)
                    post_file_paths['data'].append(path_dict)
                else:
                    logging.info("Data file's name should end with '_detection' or '_post'. excluding " + file_name)
                    excluded_files.append(p)
            else:
                logging.info("File's extension should be 'mp4' or 'xlsx'. excluding " + file_name)
                excluded_files.append(p)
        self._detection_file_paths = detection_file_paths
        self._post_file_paths = post_file_paths
        log = '\n'.join(['{}: '.format(i) + p for i, p in enumerate(self._detection_file_paths)])
        logging.info('\n Detection file paths: \n' + log)
        log = '\n'.join(['{}: Data: '.format(i) + self._post_file_paths['data'][i]['data']
                        for i in range(len(self._post_file_paths['data']))])
        logging.info('\n Postprocessing data file paths: \n' + log)
        log = '\n'.join(['{}: Data: '.format(i) + self._post_file_paths['video'][i]['data'] +
                        ', video: ' + str(self._post_file_paths['video'][i]['video'])
                        for i in range(len(self._post_file_paths['video']))])
        logging.info('\n Postprocessing video file paths: \n' + log)
        log = '\n'.join(['{}: '.format(i) + p for i, p in enumerate(excluded_files)])
        logging.info('\n Excluded file paths: \n' + log)
        try:
            self.preview_file_path = self._detection_file_paths[0]
            logging.info('Detection preview file:' + self.preview_file_path.split(os.path.sep)[-1])
        except:
            logging.info('No detection preview file')

    @property
    def detection_output_type(self):
        return self._detection_output_type

    @detection_output_type.setter
    def detection_output_type(self, detection_output_type_name):
        if detection_output_type_name in self._detection_output_type_list:
            self._detection_output_type = detection_output_type_name
            logging.info('Set detection output type:{}'.format(self._detection_output_type))
        else:
            logging.info('Detection output type not in list')

    @property
    def post_output_type(self):
        return self._post_output_type

    @post_output_type.setter
    def post_output_type(self, post_output_type_name):
        if post_output_type_name in self._post_output_type_list:
            self._post_output_type = post_output_type_name
            logging.info('Set post output type:{}'.format(self._post_output_type))
        else:
            logging.info('Post output type not in list')
