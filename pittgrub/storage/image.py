"""
Store and retrieve images in/from filesystem
"""

import os
from typing import List

from PIL import Image


class ImageStore:
    # number of subdirectory levels
    LEVELS = 3

    # upper bound for image id (must be less than this)
    BOUND = 1_000_000_000_000   # 1 trillion

    # padding for image name (12 characters long)
    PADDING = 12

    # image extension
    EXT = "jpg"

    def __init__(self, path: str, quality: int=75, optimize: bool=True):
        """
        :path: root directory for image storage
        path is created if it doesn't already exist
        :quality: jpg quality (default: 75)
        :optimize: optimize jpg size (default: True)
        """
        assert not not path, "Path must not be empty"
        self.path = path
        self.quality = quality
        self.optimize = optimize
        if not os.path.exists(path):
            os.makedirs(path)

    def get_name(self, id: int) -> str:
        """Convert image id to file name
        :id: image id
        """
        assert id is not None, "id cannot be None"
        assert id < self.BOUND, f"id too large, max is {self.BOUND}"
        return str(id).zfill(self.PADDING)  # set id length to bound

    def get_directories(self, name: str) -> List[str]:
        """Get hierarchy of directories from root where image is stored
        :name: name of image
        :return: ordered list of directories
        """
        assert len(name) == self.PADDING
        return [name[i:i+self.LEVELS]
                for i in range(0, self.PADDING-self.LEVELS, self.LEVELS)]

    def get_path(self, name: str) -> str:
        """Get relative image path as string of directories
        :name: image name
        :return: path to image
        """
        dirs = '/'.join(self.get_directories(name))
        return f'{self.path}/{dirs}'

    def get_location(self, id: int) -> str:
        """Get relative image location
        :id: image id
        :return: the/path/to/image.jpeg
        """
        image_name = self.get_name(id)
        image_path = self.get_path(image_name)
        return f'{image_path}/{image_name}.{self.EXT}'

    def save_image(self, id: int, image: Image) -> bool:
        """Save image to file system
        :id: image id
        :image: image to save (opened with PIL/PILLOW)
        """
        # convert image to jpeg
        if not (image.filename.endswith('jpg') or image.filename.endswith('jpeg')):
            image = image.convert('RGB')
        image_name = self.get_name(id)
        image_path = self.get_path(image_name)
        image_loc = self.get_location(id)
        if os.path.exists(image_path):
            if os.path.isfile(image_loc):
                return False, "Image already exists"
            else:
                image.save(image_loc, "JPEG", quality=self.quality, optimize=self.optimize)
        else:
            os.makedirs(image_path)
            image.save(image_loc, "JPEG", quality=self.quality, optimize=self.optimize)
        return True

    def update_image(self, id: int, image: Image) -> bool:
        # convert image to jpeg
        if not (image.filename.endswith('jpg') or image.filename.endswith('jpeg')):
            image = image.convert('RGB')
        image_name = self.get_name(id)
        image_path = self.get_path(image_name)
        image_loc = self.get_location(id)
        if os.path.exists(image_path):
            image.save(image_loc, "JPEG", quality=self.quality, optimize=self.optimize)
        else:
            os.makedirs(image_path)
            image.save(image_loc, "JPEG", quality=self.quality, optimize=self.optimize)
        return True

    def fetch_image(self, id: int) -> Image:
        image_name = self.get_name(id)
        image_path = self.get_path(image_name)
        image_loc = self.get_location(id)
        if os.path.exists(image_path):
            if os.path.isfile(image_loc):
                return Image.open(image_loc)
        print(f'image "{image_loc}" not found')
        return None