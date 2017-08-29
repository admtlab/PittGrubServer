"""
Store and retrieve images in/from filesystem
"""

import os
from typing import List

from PIL import Image


class ImageStore:
    # padding for image name (12 characters long)
    PADDING = 12

    # upper bound for image id (must be less than this)
    BOUND = 1_000_000_000_000   # 1 trillion

    # number of subdirectory levels
    LEVELS = 3

    # directory separator character
    # SEPARATOR = "/"

    # supported image extensions
    EXTENSIONS = ["jpg", "png"]

    def __init__(self, path: str):
        """
        path: root directory for image storage
        """
        assert path is not None and not path == "", "Path must not be empty"

        self.path = path
        if not os.path.exists(path):
            os.makedirs(path)

    def get_name(self, id: int, ext: str='jpg') -> str:
        """Convert image id to file name
        :id: image id
        :ext: image extension
        """
        assert id is not None, "id cannot be None"
        assert id < self.BOUND, f"id too large, max is {self.BOUND}"
        assert ext[-3:] in self.EXTENSIONS, f"Image must be one of the following extensions: {self.EXTENSIONS}"

        if not ext.startswith('.'): ext = '.' + ext
        return str(id).zfill(self.PADDING) + ext

    def get_directories(self, name: str) -> List[str]:
        """Get heirarchy of directories from root where image is stored
        :name: name of image
        :return: ordered list of directories
        """
        assert len(name) == self.PADDING
        return [name[i:i+self.LEVELS]
                for i in range(0, self.PADDING-self.LEVELS)]

    def get_path(self, name: str) -> str:
        """Get relative image path as string of directories
        :name: image name
        :return: path to image
        """
        dirs = '/'.join(self.get_directories(name))
        return f'{self.path}/{dirs}'

    def get_location(self, id: int, ext: str) -> str:
        """Get relative image location
        :id: image id
        :ext: image extension
        :return: the/path/to/image.ext
        """
        image_name = self.get_name(id, ext)
        image_path = self.get_path(image_name)
        return f'{image_path}/{image_name}'

    def store_image(self, id: int, ext: str, image: Image) -> bool:
        image_name = get_name(id, ext)
        image_path = get_path(image_name)
        image_loc = get_location(id, ext)
        if os.path.exists(image_path):
            if os.path.isfile(image_loc):
                return False, "Image already exists"
            else:
                image.save(image_loc)
        else:
            os.path.makedirs(image_path)
            image.save(image_loc)
        return True

    def update_image(self, id: int, ext: str, image: Image) -> bool:
        image_name = get_name(id, ext)
        image_path = get_path(image_name)
        image_loc = get_location(id, ext)
        if os.path.exists(image_path):
            image.save(image_loc)
        else:
            os.path.makedirs(image_path)
            image.save(image_loc)
        return True

    def fetch_image(self, id: int, ext: str) -> 'Image':
        image_name = get_name(id, ext)
        image_path = get_path(image_name)
        image_loc = get_location(id, ext)
        if os.path.exists(image_path):
            if os.path.isfile(image_loc):
                img = Image.open(image_loc)
                img.show()
                return
        print(f'image "{image_loc}" not found')
        return None
