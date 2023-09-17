import os
import random
from pathlib import Path
from matplotlib.image import imread, imsave
import random


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j - 1] - row[j]))

            self.data[i] = res

    def rotate(self):
        result = []
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(self.data[j][i])
            for k in range(0, len(res) // 2):
                temp = res[k]
                res[k] = res[len(res) - k - 1]
                res[len(res) - k - 1] = temp
            result.append(res)
        self.data = result

    def salt_n_pepper(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(0, len(row)):
                randomber = random.random()
                if randomber < 0.2:
                    res.append(255)  # Add salt noise (white)
                elif randomber > 0.8:
                    res.append(0)  # Add pepper noise (black)
                else:
                    res.append(row[j])  # Keep the original pixel value

            self.data[i] = res

    def concat(self, other_img, direction='horizontal'):
        firstimage = self.data
        secondimage = other_img.data
        if (len(firstimage) != len(secondimage)) or (len(firstimage[0]) != len(secondimage[0])):
            raise RuntimeError
        else:
            if direction == 'horizontal':
                arr = []
                for i, row in enumerate(self.data):
                    res = []
                    for j in range(0, len(row)):
                        res.append(self.data[i][j])
                    for k in range(0, len(row)):
                        res.append(other_img.data[i][k])
                    arr.append(res)
                self.data = arr

    def segment(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(0, len(row)):
                if self.data[i][j] > 100:
                    res.append(255)
                else:
                    res.append(0)

            self.data[i] = res


if __name__ == "__main__":
    my_img = Img('C:/Users/97254/Documents/Image Processing/ImageProcessingService/polybot/test/beatles.jpeg')
    my_img.salt_n_pepper()
    my_img.save_img()  # noisy image was saved in 'path/to/image_filtered.jpg'