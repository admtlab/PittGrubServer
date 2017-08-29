"""
Store and retrieve images in/from filesystem
"""

import os
from typing import List


class ImageStore:
    # padding for image name (12 characters long)
    PADDING = 12

    # upper bound for image id (must be less than this)
    BOUND = 1_000_000_000_000   # 1 trillion

    # number of subdirectory levels
    LEVELS = 3

    # directory separator character
    SEPARATOR = "/"

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

    def _get_image_name(self, id: int, ext: str='jpg') -> str:
        """Convert image id to file name
        id: image id
        ext: image extension
        """
        assert id is not None, "I cannot be none"
        assert id < BOUND, f"Id too large, max is {self.BOUND}"
        assert ext.replace('.','') in self.EXTENSIONS,
            f"Image must be one of the following extensions: {self.EXTENSIONS}"

        if not ext.startswith('.'): ext = '.' + ext
        return str(id).zfill(PADDING) + ext

    def _get_image_dir(self, name: str) -> List[str]:
        assert len(name) == PADDING
        return SEPARATOR.join([name[i:i+chunk_size] for i in range(0, PADDING-LEVELS, LEVELS)])

    def image_location(self, id: int, ext: str) -> str:
        image_name = self._get_image_name(id, ext)
        image_path = self._get_image_dir(image_name)
        return f'{self.path}/{image_path}/{image_name}'

    def store_image(self, id: int, ext: str, image: 'Image') -> bool:
        assert id < BOUND



    def fetch_image(self, id: int, ext: str) -> 'Image':
        image_name = get_image_name(id, ext)
        image_path = get_image_path(image_name)
