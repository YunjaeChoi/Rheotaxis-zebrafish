import numpy as np
import cv2

from zebrafish.utils import convert_angle

class ThresholdDetector(object):

    def __init__(self,
                 l_thresh=(0, 70),
                 size_bound=(130, 310),
                 median_blur_size=3,
                 closing_iterations=5):

        #get_angle params
        self.l_thresh = l_thresh
        self.size_bound = size_bound #for pixel calculations
        #self.denoising_kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        self.denoising_kernel = np.array([[0,1,0],
                                          [1,1,1],
                                          [0,1,0]], dtype=np.uint8)
        self.closing_kernel = np.array([[0,1,0],
                                        [1,1,1],
                                        [0,1,0]], dtype=np.uint8)
        self.closing_iterations = closing_iterations
        self.median_blur_size = median_blur_size

        self.ang_draw_ratio = 2.

    def process_image(self, img):
        #to hls
        #hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
        #l_channel = hls[:,:,1]

        #to lab
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2Lab)
        l_channel = lab[:,:,0]

        #blur
        blur = cv2.medianBlur(l_channel, self.median_blur_size)

        #l thresholding
        l_binary = np.zeros_like(blur)
        l_binary[(blur >= self.l_thresh[0]) & (blur <= self.l_thresh[1])] = 1

        #closing opening (denoising)
        closing = cv2.morphologyEx(l_binary, cv2.MORPH_CLOSE, self.denoising_kernel)
        opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, self.denoising_kernel)

        #closing
        dilation = cv2.dilate(opening, self.closing_kernel, iterations=self.closing_iterations)
        erosion = cv2.erode(dilation, self.closing_kernel, iterations=self.closing_iterations)
        return lab, l_channel, blur, l_binary, closing, opening, dilation, erosion

    def detect_countours_hulls_moments(self, binary_img):
        _, contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        convex_hulls = [cv2.convexHull(cnt) for cnt in contours]
        hull_moments = [cv2.moments(hull) for hull in convex_hulls]
        return contours, convex_hulls, hull_moments

    def bound_hulls_by_size(self, convex_hulls, hull_moments):
        bound_bool = [self.size_bound[0] <= hm['m00'] <= self.size_bound[1] for hm in hull_moments]
        convex_hulls_bounded = [convex_hulls[i]  for i in range(len(bound_bool)) if bound_bool[i]]
        hull_moments_bounded = [hull_moments[i]  for i in range(len(bound_bool)) if bound_bool[i]]
        return convex_hulls_bounded, hull_moments_bounded

    def get_position_and_angle_from_hulls(self, convex_hulls, hull_moments):
        #position in image coord, x=m['m10']/m['m00'], y=m['m01']/m['m00']
        position = np.array([[m['m10']/m['m00'], m['m01']/m['m00']] for m in hull_moments])

        #angle vector
        hulls_reshaped = [np.squeeze(hull, axis=-2) for hull in convex_hulls]
        dists = [np.linalg.norm(hulls_reshaped[i] - position[i], axis=-1) for i in range(len(hulls_reshaped))]
        max_dist_idxs = [np.argmax(d, axis=-1) for d in dists]
        max_dist_hull_points = np.array([hulls_reshaped[i][max_dist_idxs[i]] for i in range(len(hulls_reshaped))])
        angle_vector = position - max_dist_hull_points
        if len(angle_vector) > 0:
            angle = np.arctan2(angle_vector[:, 1], angle_vector[:, 0])
        else:
            angle = angle_vector
        return position, angle, hulls_reshaped, angle_vector

    def detect_position_and_angle(self, img):
        processed_images = self.process_image(img)

        #contour
        contours, convex_hulls, hull_moments = self.detect_countours_hulls_moments(processed_images[-1])

        #bound by size
        convex_hulls_bounded, hull_moments_bounded = self.bound_hulls_by_size(convex_hulls, hull_moments)

        #position, angle
        position, angle, hulls_reshaped, angle_vector = self.get_position_and_angle_from_hulls(convex_hulls_bounded, hull_moments_bounded)
        return position, angle, hulls_reshaped, angle_vector

    def convert_hulls_to_bboxes(self, hulls_list):
        #bbox:(x,y,w,h), (x,y):top left, (w,h): width, height
        bboxes = np.array([cv2.boundingRect(h) for h in hulls_list])

        #bbox conv:(x1,y1,x2,y2), (x1,y1):top left, (x2,y2):bottom right
        bboxes_converted = np.copy(bboxes)
        bboxes_converted[:, 2] += bboxes[:, 0]
        bboxes_converted[:, 3] += bboxes[:, 1]
        return bboxes_converted

    def get_processing_step_images(self, img):
        processed_images = self.process_image(img)
        lab, l_channel, blur, l_binary, closing, opening, dilation, erosion = processed_images

        #contour
        contours, convex_hulls, hull_moments = self.detect_countours_hulls_moments(processed_images[-1])

        #bound by size
        #convex_hulls_bounded, hull_moments_bounded = self.bound_hulls_by_size(convex_hulls, hull_moments)

        position = np.array([[m['m10']/m['m00'], m['m01']/m['m00']] for m in hull_moments])

        for i in range(len(hull_moments)):
            cv2.drawContours(img, [convex_hulls[i]], 0, (0,255,0), 1)
            if self.size_bound[0] <= hull_moments[i]['m00'] <= self.size_bound[1]:
                cv2.putText(img, '{:.1f}, in.'.format(hull_moments[i]['m00']),
                            tuple(position[i].astype(np.int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
            else:
                cv2.putText(img, '{:.1f}, out.'.format(hull_moments[i]['m00']),
                            tuple(position[i].astype(np.int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 2)
        return l_channel, blur, l_binary, erosion, img

    def get_preview_images(self, img, overall_crop):
        cropped_img = img[overall_crop[0,0]:overall_crop[1,0],
                                  overall_crop[0,1]:overall_crop[1,1],:]

        l_channel_img = np.copy(img)
        blur_img = np.copy(img)
        l_binary_img = np.copy(img)
        closing_img = np.copy(img)
        result_img = np.copy(img)

        step_cropped_images = self.get_processing_step_images(cropped_img)

        l_channel_stack = np.stack([step_cropped_images[0] for i in range(3)], axis=-1)

        l_channel_img[overall_crop[0,0]:overall_crop[1,0],
                      overall_crop[0,1]:overall_crop[1,1],:] = l_channel_stack

        blur_stack = np.stack([step_cropped_images[1] for i in range(3)], axis=-1)

        blur_img[overall_crop[0,0]:overall_crop[1,0],
                 overall_crop[0,1]:overall_crop[1,1],:] = blur_stack

        l_binary_stack = np.stack([step_cropped_images[2] for i in range(3)], axis=-1)
        l_binary_stack *= 255

        l_binary_img[overall_crop[0,0]:overall_crop[1,0],
                     overall_crop[0,1]:overall_crop[1,1],:] = l_binary_stack

        closing_stack = np.stack([step_cropped_images[3] for i in range(3)], axis=-1)
        closing_stack *= 255

        closing_img[overall_crop[0,0]:overall_crop[1,0],
                    overall_crop[0,1]:overall_crop[1,1],:] = closing_stack

        result_img[overall_crop[0,0]:overall_crop[1,0],
                   overall_crop[0,1]:overall_crop[1,1],:] = step_cropped_images[4]
        cv2.rectangle(result_img, (overall_crop[0,1], overall_crop[0,0]),
                      (overall_crop[1,1], overall_crop[1,0]), (255, 0, 0), 4)

        step_images = [l_channel_img, blur_img, l_binary_img, closing_img, result_img]
        step_names = ['l_channel', 'blur', 'l_binary', 'closing', 'result_img']
        return step_images, step_names

    def get_every_processing_step_images(self, img):
        processed_images = self.process_image(img)
        lab, l_channel, blur, l_binary, closing, opening, dilation, erosion = processed_images

        #contour
        contours, convex_hulls, hull_moments = self.detect_countours_hulls_moments(processed_images[-1])

        #bound by size
        convex_hulls_bounded, hull_moments_bounded = self.bound_hulls_by_size(convex_hulls, hull_moments)

        #position, angle
        position, angle, hulls_reshaped, angle_vector = self.get_position_and_angle_from_hulls(convex_hulls_bounded, hull_moments_bounded)

        #bbox
        bboxes = self.convert_hulls_to_bboxes(hulls_reshaped)

        img_bbox = np.copy(img)
        #draw bbox
        for i in range(len(bboxes)):
            top_left = tuple(bboxes[i, :2])
            bottom_right = tuple(bboxes[i, 2:])
            cv2.rectangle(img_bbox, top_left, bottom_right, (0, 255, 0), 1)

        #draw hulls
        cv2.polylines(img, hulls_reshaped, True, (0, 255, 0), 1)

        img_hull = np.stack([erosion*255]*3, axis=-1)
        cv2.polylines(img_hull, hulls_reshaped, True, (0, 255, 0), 1)

        img_hull_with_pos = np.copy(img)
        img_hull_with_angle = np.copy(img)

        #draw position
        position_int = position.astype(np.int)
        position_int_list = [tuple(p) for p in position_int]
        for i in range(len(position_int_list)):
            #cv2.circle(img_hull_with_pos, position_int_list[i], 1, (0, 0, 255), -1)
            cv2.circle(img_hull_with_pos, position_int_list[i], 2, (255,0,0), thickness=2)

        #draw angle vectors
        arrow_start_points = (position - angle_vector).astype(np.int)
        arrow_end_points = (arrow_start_points + self.ang_draw_ratio * angle_vector).astype(np.int)
        start_point_list = [tuple(p) for p in arrow_start_points]
        end_point_list = [tuple(p) for p in arrow_end_points]
        for i in range(len(start_point_list)):
            cv2.arrowedLine(img_hull_with_angle, start_point_list[i], end_point_list[i],
                            (255, 0, 0), 1)

        return l_channel, blur, l_binary, opening, erosion, img_hull, img_hull_with_pos, img_hull_with_angle, img_bbox

    def draw_detection_img(self, img,
                           zero_angle='left',
                           ang_text_y_diff=50,
                           text_font_size=1.0):
        position, angle, hulls, angle_vector = self.detect_position_and_angle(img)
        _, rel_ang_deg = convert_angle(angle, zero_angle=zero_angle)

        if len(position) > 0:
            #draw contours
            cv2.polylines(img, hulls, True, (0, 255, 0), 1)

            #draw angle vectors
            arrow_start_points = (position - angle_vector).astype(np.int)
            arrow_end_points = (arrow_start_points + 2.0 * angle_vector).astype(np.int)
            start_point_list = [tuple(p) for p in arrow_start_points]
            end_point_list = [tuple(p) for p in arrow_end_points]
            for i in range(len(start_point_list)):
                cv2.arrowedLine(img, start_point_list[i], end_point_list[i],
                                (255, 0, 0), 1)

            #draw position
            position_int = position.astype(np.int)
            position_int_list = [tuple(p) for p in position_int]
            for i in range(len(position_int_list)):
                #cv2.circle(img, position_int_list[i], 1, (0, 0, 255), -1)
                cv2.circle(img, position_int_list[i], 15, (0,255,0), thickness=2)

            #draw text
            ang_text_pos = position_int + ang_text_y_diff
            ang_text_pos_list = [tuple(p) for p in ang_text_pos]
            ang_text_diff = np.zeros_like(ang_text_pos)
            ang_text_diff[:, 1] += ang_text_y_diff
            rel_ang_text_pos_list = [tuple(p) for p in ang_text_pos + ang_text_diff]
            for i in range(len(position)):
                cv2.putText(img, '{:.2f}, {:.2f}'.format(position[i][0], position[i][1]), position_int_list[i],
                            cv2.FONT_HERSHEY_SIMPLEX, text_font_size, (0,0,255), 2)
                cv2.putText(img, '{:.3f}'.format(angle[i]), ang_text_pos_list[i],
                            cv2.FONT_HERSHEY_SIMPLEX, text_font_size, (0,0,255), 2)
                cv2.putText(img, '{:.2f}'.format(rel_ang_deg[i]), rel_ang_text_pos_list[i],
                            cv2.FONT_HERSHEY_SIMPLEX, text_font_size, (0,0,255), 2)
        return img
