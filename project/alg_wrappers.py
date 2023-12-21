import cv2
import math

from algorithms.basic_lsb import lsb_basic_hide, lsb_basic_reveal
from algorithms.variable_rate_lsb import lsb_vr_count_available_bits, lsb_vr_hide, lsb_vr_reveal
from algorithms.coverless import hide_data


def lsb_basic_hide_wrapper(im1, im2, color_proportion):
    bit_fraction_used = sum(color_proportion)/24
    new_x, new_y = int(im1.shape[0] * math.sqrt(bit_fraction_used)), int(im1.shape[1] * math.sqrt(bit_fraction_used))
    if new_x < im2.shape[0] or new_y < im2.shape[0]:
        im2 = cv2.resize(im2.copy(), (new_x, new_y))
    
    return lsb_basic_hide(im1, im2, color_proportion)

def lsb_basic_reveal_wrapper(im, color_proportion):
    bit_fraction_used = sum(color_proportion)/24
    hidden_shape = int(im.shape[0] * math.sqrt(bit_fraction_used)), int(im.shape[1] * math.sqrt(bit_fraction_used)), im.shape[2]

    return lsb_basic_reveal(im, hidden_shape, color_proportion)

def lsb_vr_hide_wrapper(im1, im2, alpha, max_p):
    bit_fraction_used = lsb_vr_count_available_bits(im1, alpha, max_p) / (im1.shape[0] * im1.shape[1] * im1.shape[2] * 8)
    new_x, new_y = int(im1.shape[0] * math.sqrt(bit_fraction_used)), int(im1.shape[1] * math.sqrt(bit_fraction_used))
    if new_x < im2.shape[0] or new_y < im2.shape[0]:
        im2 = cv2.resize(im2.copy(), (new_x, new_y))

    return lsb_vr_hide(im1, im2, alpha, max_p)

def lsb_vr_reveal_wrapper(im, alpha, max_p):
    bit_fraction_used = lsb_vr_count_available_bits(im, alpha, max_p) / (im.shape[0] * im.shape[1] * im.shape[2] * 8)
    hidden_shape = int(im.shape[0] * math.sqrt(bit_fraction_used)), int(im.shape[1] * math.sqrt(bit_fraction_used)), im.shape[2]

    return lsb_vr_reveal(im, hidden_shape, alpha, max_p)

def coverless_hide_data_wrapper(image, data, cache, progress_queue):
    result_im = image.copy()
    hide_data(result_im, data, cache, progress_queue)
    return result_im
