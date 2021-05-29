import numpy as np
import pandas as pd
import logging

class DataSaver(object):

    def __init__(self):
        self._video_path = None
        self.output_file_path = None
        #self.excel_writer = None
        self.output_file_suffix = '_output_data'

    def save(self):
        pass


class DetectionDataSaver(DataSaver):

    def __init__(self):
        super(DetectionDataSaver, self).__init__()
        self.data = []
        self.output_file_suffix = '_detection'

        self.base_data_names = ['frame_num']
        self.input_data_names = ['pos_x_in_crop',
                                 'pos_y_in_crop',
                                 'pos_x_in_frame',
                                 'pos_y_in_frame',
                                 'bbox_tl_x_in_crop',
                                 'bbox_tl_y_in_crop',
                                 'bbox_br_x_in_crop',
                                 'bbox_br_y_in_crop',
                                 'angle',
                                 'angle_vector_x',
                                 'angle_vector_y',
                                 'rel_angle_rad',
                                 'rel_angle_deg']
        self.input_data_names_idx = dict((name, i) for i, name in enumerate(self.input_data_names))

        self.data_names = self.base_data_names + self.input_data_names
        self.data_names_idx = dict((name, i) for i, name in enumerate(self.data_names))

    def add_data_by_frame(self, input_data, frame_num):
        frame_num_array = np.zeros((input_data.shape[0], 1)) + frame_num
        data = np.concatenate([frame_num_array, input_data], axis=-1)
        self.data.append(data)

    def save(self):
        #save data
        data = np.concatenate(self.data, axis=0)
        data = pd.DataFrame(data, columns=self.data_names)
        #data.to_excel(self.excel_writer, 'data', index=False)
        #self.excel_writer.save()
        data.to_excel(self.output_file_path + '.xlsx', sheet_name='data', index=False)
        data.to_csv(self.output_file_path + '.csv', index=False)
        logging.info('Detection data saved at: ' + self.output_file_path)

    def clear(self):
        self.data = []

    @property
    def video_path(self):
        return self._video_path

    @video_path.setter
    def video_path(self, path):
        self._video_path = path
        self.output_file_path = self._video_path.split('.')[0] + self.output_file_suffix
        #self.excel_writer = pd.ExcelWriter(self.output_file_path + '.xlsx')

class PostprocessDataSaver(DataSaver):

    def __init__(self):
        super(PostprocessDataSaver, self).__init__()
        self.output_file_suffix = '_post'
        self._post_data_path = None

    def save(self, data):
        #data.to_excel(self.excel_writer, 'data', index=False)
        #self.excel_writer.save()
        data.to_excel(self.output_file_path + '.xlsx', sheet_name='data', index=False)
        data.to_csv(self.output_file_path + '.csv', index=False)
        logging.info('Postprocessed data saved at: ' + self.output_file_path)

    @property
    def post_data_path(self):
        return self._post_data_path

    @post_data_path.setter
    def post_data_path(self, path):
        self._post_data_path = path
        self.output_file_path = self._post_data_path.split('.')[0] + self.output_file_suffix
        #self.excel_writer = pd.ExcelWriter(self.output_file_path + '.xlsx')
