import numpy as np

def coords_from_ctr(ctr, h, w, d):
    return ctr%8, ctr//8%d, ctr//(8*d)%w, ctr//(8*d*w)%h

def lsb_vr_hide(im1, im2, alpha=9, max_p=4):
    h1, w1, d1 = im1.shape
    h2, w2, d2 = im2.shape
    
    im3 = im1.copy()
    
    im2_ctr = 0
    
    for row in range(2, h1 - 1):
        for col in range(2 + row%2, w1 - 1, 2):
            for d in range(d1):
                x = im1[row - 1, col, d] ^ im1[row + 1, col, d] ^ im1[row, col - 1, d] ^ im1[row, col + 1, d]
                p = 1
                if x > alpha:
                    p = min(max_p, int(np.ceil(x/2)))
                
                b = im3[row, col, d]
                b = ((b>>p)<<p) # Wipe p LSBits from b
                for j in range(p - 1, -1, -1):
                    b2, z2, y2, x2 = coords_from_ctr(im2_ctr, h2, w2, d2)
                    b = b | (((im2[x2, y2, z2]>>(7 - b2))&1)<<j) # Take b2-th MSB of im2 pixel and insert it at j-th LSB of b
                    im2_ctr += 1
                    if im2_ctr == h2*w2*d2*8:
                        im3[row, col, d] = b
                        return im3
                im3[row, col, d] = b
    return im3

def lsb_vr_reveal(im, hidden_shape, alpha=9, max_p=4):
    h1, w1, d1 = im.shape
    h2, w2, d2 = hidden_shape
        
    res = np.zeros(hidden_shape, dtype=np.uint8)
    
    im2_ctr = 0
    res_b = 0
    
    for row in range(2, h1 - 1):
        for col in range(2 + row%2, w1 - 1, 2):
            for d in range(d1):
                x = im1[row - 1, col, d] ^ im1[row + 1, col, d] ^ im1[row, col - 1, d] ^ im1[row, col + 1, d]
                p = 1
                if x > alpha:
                    p = min(max_p, int(np.ceil(x/2)))
                
                b = im[row, col, d]
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
