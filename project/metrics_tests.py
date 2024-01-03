from skimage.metrics import peak_signal_noise_ratio, mean_squared_error, structural_similarity
from sklearn.metrics import mean_absolute_error
import cv2
import numpy as np 
import pathlib
import re
import pandas as pd
import math
from algorithms.variable_rate_lsb import lsb_vr_count_available_bits


misc_mapping = {
    "paprica": "../misc/4.2.07.tiff",
    "boat": "../misc/4.2.06.tiff",
    "people": "../misc/4.1.02.tiff",
    "plane": "../misc/4.2.05.tiff",
    "woman": "../misc/4.1.03.tiff",
    "splash": "../misc/4.2.01.tiff",
}

misc_shapes = {
    "paprica": (512, 512),
    "boat": (512, 512),
    "people": (256, 256),
    "plane": (512, 512),
    "woman": (256, 256),
    "splash": (512, 512),
}

def read_im(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def NCC(cover_im, stego_im):
    return np.sum(cover_im * stego_im) / np.sum(np.square(stego_im))

def get_metrics(cover_name, stego_name):
    cover_im = read_im(cover_name)
    stego_im = read_im(stego_name)

    psnr = peak_signal_noise_ratio(cover_im, stego_im)
    mse = mean_squared_error(cover_im, stego_im)
    rmse = np.sqrt(mean_squared_error(cover_im, stego_im))
    mae = mean_absolute_error(cover_im.flatten(), stego_im.flatten())
    ssim = structural_similarity(cover_im, stego_im, channel_axis=2)
    ncc = NCC(cover_im, stego_im)

    return psnr, mse, rmse, mae, ssim, ncc

def basic_lsb_result_ratio(cover_shape, hidden_shape, color_proportion):
    bit_fraction_used = sum(color_proportion)/24
    return int(cover_shape[0] * math.sqrt(bit_fraction_used)) / hidden_shape[0]

def vr_lsb_result_ratio(cover_name, hidden_shape, alpha, max_p):
    cover_im = read_im(cover_name)
    cover_shape = cover_im.shape
    bit_fraction_used = lsb_vr_count_available_bits(cover_im, alpha, max_p) / (cover_shape[0] * cover_shape[1] * cover_shape[2] * 8)
    return int(cover_shape[0] * math.sqrt(bit_fraction_used)) / hidden_shape[0]

def basic_lsb_metrics():
    basic_params = ["111", "222", "234", "333", "246", "444", "666"]
    basic_path = "../basic_tests_images"
    files_metrics = {}
   
    print("Basic LSB:") 
    for filename in pathlib.Path(basic_path).iterdir():
        cover_name, hidden_name, params = re.search(r"(.*)_(.*)_basic_(.*).tiff", filename.name).groups()
        metrics = get_metrics(misc_mapping[cover_name], str(filename))
        if cover_name not in files_metrics:
            files_metrics[cover_name] = [None]*len(basic_params)
        params_tuple = int(params[0]), int(params[1]), int(params[2])
        ratio = basic_lsb_result_ratio(misc_shapes[cover_name], misc_shapes[hidden_name], params_tuple)
        files_metrics[cover_name][basic_params.index(params)] = (ratio,) + metrics
    
    for file, metrics in files_metrics.items():
        print(f"{file}:")
        df = pd.DataFrame(metrics, columns=['ratio', 'PSNR', 'MSE', 'RMSE', 'MAE', 'SSIM', 'NCC'], index=basic_params)
        df.index.name = 'RGB'
        print(df, end="\n\n")

def vr_lsb_metrics():
    vr_params = ["202", "22", "204", "104", "94", "44", "106", "26"]
    vr_path = "../vr_tests_images"
    files_metrics = {}

    print("VR LSB:")
    for filename in pathlib.Path(vr_path).iterdir():
        cover_name, hidden_name, params = re.search(r"(.*)_(.*)_vr_(.*).tiff", filename.name).groups()
        metrics = get_metrics(misc_mapping[cover_name], str(filename))
        if cover_name not in files_metrics:
            files_metrics[cover_name] = [None]*len(vr_params)
        alpha, max_p = int(params[:-1]), int(params[-1])
        ratio = vr_lsb_result_ratio(misc_mapping[cover_name], misc_shapes[hidden_name], alpha, max_p)
        files_metrics[cover_name][vr_params.index(params)] = (ratio,) + metrics
    
    for file, metrics in files_metrics.items():
        print(f"{file}:")
        df = pd.DataFrame(metrics, columns=['ratio', 'PSNR', 'MSE', 'RMSE', 'MAE', 'SSIM', 'NCC'], index=[f"{p[:-1]: >2}, {p[-1]: >2}" for p in vr_params])
        df.index.name = ' a, mb'
        print(df, end="\n\n")


if __name__ == "__main__":
    basic_lsb_metrics()
    vr_lsb_metrics()
