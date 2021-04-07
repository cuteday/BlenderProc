from src.main.Module import Module
import numpy as np

class AvgRedundantChannels(Module):
    """ Removes redundant channels, where the input has more than one channels that share exactly the same value """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The trimmed image data.
        """
        # In case that values among channels is fluctuating, we calculate the average for better stablity
        rows, cols, chs = image.shape
        if chs > 3:
            raise Exception('AvgRedundantChannels: The image has more than 3 channels? Ov0')
        image = np.average(image, axis=-1) 

        return image, key, version
