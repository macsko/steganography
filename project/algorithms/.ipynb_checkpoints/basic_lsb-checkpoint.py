import numpy as np

def coords_from_ctr(ctr, h, w, d):
    return ctr%8, ctr//8%d, ctr//(8*d)%w, ctr//(8*d*w)%h

def lsb_basic_hide(im1, im2, color_proportion=None):
    h1, w1, d1 = im1.shape
    h2, w2, d2 = im2.shape
    
    if color_proportion is None:
        color_proportion = [8*h2//h1]*3
        
    im3 = im1.copy()
    im2_ctr = 0
    
    for x1 in range(h1):
        for y1 in range(w1):
            for z1 in range(d1):
                b = im3[x1, y1, z1]
                p = color_proportion[z1]
                b = ((b>>p)<<p) # Wipe p LSBits from b
                for j in range(p - 1, -1, -1):
                    b2, z2, y2, x2 = coords_from_ctr(im2_ctr, h2, w2, d2)
                    b = b | (((im2[x2, y2, z2]>>(7 - b2))&1)<<j) # Take b2-th MSB of im2 pixel and insert it at j-th LSB of b
                    im2_ctr += 1
                    if im2_ctr == h2*w2*d2*8:
                        im3[x1, y1, z1] = b
                        return im3
                                    
                im3[x1, y1, z1] = b
    return im3

def lsb_basic_reveal(im, hidden_shape, color_proportion=None):
    h1, w1, d1 = im.shape
    h2, w2, d2 = hidden_shape
    
    if color_proportion is None:
        color_proportion = [8*h2//h1]*3
        
    res = np.zeros(hidden_shape, dtype=np.uint8)
    res_b = 0
    im2_ctr = 0
    
    for x1 in range(h1):
        for y1 in range(w1):
            for z1 in range(d1):
                b = im[x1, y1, z1]
                p = color_proportion[z1]
                for j in range(p - 1, -1, -1):
                    b2, z2, y2, x2 = coords_from_ctr(im2_ctr, h2, w2, d2)
                    res_b = res_b | (((b>>j)&1) << (7 - b2)) # Take j-th LSB of b and insert it at b2-th MSG of res_b
                    
                    im2_ctr += 1
                    if b2 == 7:
                        res[x2, y2, z2] = res_b
                        res_b = 0
                    if im2_ctr == h2*w2*d2*8:
                        return res
                                    
    return res
