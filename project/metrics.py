from skimage.metrics import peak_signal_noise_ratio, mean_squared_error, structural_similarity
from sklearn.metrics import mean_absolute_error
import sys
import cv2
import numpy as np 

def read_im(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def ncc(cover_im, stego_im):
    return np.sum(cover_im * stego_im) / np.sum(np.square(stego_im))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python metrics.py <cover_image> <stego_image>")
        sys.exit(1)
    
    cover_im = read_im(sys.argv[1])
    stego_im = read_im(sys.argv[2])

    print(f"Image quality metrics for {sys.argv[1]} and {sys.argv[2]}:")
    print("PSNR:", peak_signal_noise_ratio(cover_im, stego_im))
    print("MSE: ", mean_squared_error(cover_im, stego_im))
    print("RMSE:", np.sqrt(mean_squared_error(cover_im, stego_im)))
    print("MAE: ", mean_absolute_error(cover_im.flatten(), stego_im.flatten()))
    print("SSIM:", structural_similarity(cover_im, stego_im, channel_axis=2))
    print("NCC: ", ncc(cover_im, stego_im))
