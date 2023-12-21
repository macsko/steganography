import cv2
import re


def get_block_with_hash(image, x, y):
    center_value = image[x][y][0]

    def to_bit(pixel_value):
        if pixel_value >= center_value:
            return 1
        else:
            return 0

    block = (
        (image[x-1][y+1][0], image[x][y+1][0], image[x+1][y+1][0]),
        (image[x-1][y][0], image[x][y][0], image[x+1][y][0]),
        (image[x-1][y-1][0], image[x][y-1][0], image[x+1][y-1][0])
    )

    bits = [to_bit(image[x - 1][y][0]),
            to_bit(image[x - 1][y - 1][0]),
            to_bit(image[x][y - 1][0]),
            to_bit(image[x + 1][y - 1][0]),
            to_bit(image[x + 1][y][0]),
            to_bit(image[x + 1][y + 1][0]),
            to_bit(image[x][y + 1][0]),
            to_bit(image[x - 1][y + 1][0])]

    lbp = 0
    bit_values = [1, 2, 4, 8, 16, 32, 64, 128]
    for i in range(len(bits)):
        lbp += bits[i] * bit_values[i]

    hash = 0
    if center_value > lbp:
        hash = 1
    else:
        hash = 0

    return block, hash


def build_block_cache(filenames, progress_queue):
    cache = {
        0: set(),
        1: set()
    }

    files_len = len(filenames)
    for i, f in enumerate(filenames):
        progress_queue.put_nowait(i / files_len)
        im = cv2.imread(f)
        blocks_with_hashes = get_blocks_with_hashes(im)
        for block, hash in blocks_with_hashes:
            cache[hash].add(block)

    return cache


def get_blocks_with_hashes(image):
    height, width, _ = image.shape
    num_of_blocks_horizontal = width // 3
    num_of_blocks_vertical = height // 3

    blocks_with_hashes = []
    for i in range(num_of_blocks_horizontal):
        for j in range(num_of_blocks_vertical):
            x = i * 3 + 1
            y = j * 3 + 1
            block, hash = get_block_with_hash(image, x, y)
            blocks_with_hashes.append((block, hash))

    return blocks_with_hashes


def get_mse(block1, block2):
    mse = 0
    for i in range(3):
        for j in range(3):
            mse += (int(block1[i][j]) - int(block2[i][j]))**2

    return mse


def get_block_for_substitution(block, hash, cache):
    min_mse = 1_000_000_000
    min_block = None
    for candidate in cache[hash]:
        candidate_mse = get_mse(block, candidate)
        if candidate_mse < min_mse:
            min_mse = candidate_mse
            min_block = candidate

    return min_block


def substitute_block(image, block, x, y): #x, y - center of block to be substituted
    for color in range(3):
        image[x-1][y+1][color] = block[0][0]
        image[x][y+1][color] = block[0][1]
        image[x+1][y+1][color] = block[0][2]
        image[x-1][y][color] = block[1][0]
        image[x][y][color] = block[1][1]
        image[x+1][y][color] = block[1][2]
        image[x-1][y-1][color] = block[2][0]
        image[x][y-1][color] = block[2][1]
        image[x+1][y-1][color] = block[2][2]


def data_to_bit_array(data):
    arr = data.encode()
    res = []
    for byte in arr:
        for val in [1, 2, 4, 8, 16, 32, 64, 128]:
            res.append(int((byte & val) > 0))

    return res


def bit_array_to_data(bit_array):
    res = []
    for i in range(len(bit_array) // 8):
        c = 0
        for index, val in enumerate([1, 2, 4, 8, 16, 32, 64, 128]):
            c += bit_array[i * 8 + index] * val
        res.append(c)

    tmp = str(bytearray(res))
    m = re.search("(?<=^bytearray\(b\').*(?=\'\)$)", tmp)
    return m.group(0)


def hide_data(image, data, cache, progress_queue):
    height, width, _ = image.shape
    num_of_blocks_horizontal = width // 3
    num_of_blocks_vertical = height // 3
    num_of_blocks = num_of_blocks_horizontal * num_of_blocks_vertical

    if len(data) / 8 > num_of_blocks:
        raise Exception(f"Image too small to hide data of size {len(data)}")

    bit_array = data_to_bit_array(data)
    bits_len = len(bit_array)
    blocks_with_hashes = get_blocks_with_hashes(image)
    for index, bit in enumerate(bit_array):
        progress_queue.put_nowait(index / bits_len)
        
        block, hash = blocks_with_hashes[index]
        if bit != hash:
            block_for_substitution = get_block_for_substitution(block, bit, cache)
            x = (index // num_of_blocks_horizontal) * 3 + 1
            y = (index % num_of_blocks_horizontal) * 3 + 1
            substitute_block(image, block_for_substitution, x, y)


def get_message(image):
    hashes = list(map(lambda x: x[1], get_blocks_with_hashes(image)))
    return bit_array_to_data(hashes)
