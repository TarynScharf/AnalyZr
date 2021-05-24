import os

from src.model.image_type import ImageType


def get_extension(file_path):
    file_name = get_name(file_path)
    return os.path.splitext(file_name)[1]

def get_name(file_path):
    return os.path.basename(file_path)

def get_folder(file_path):
    return os.path.dirname(file_path)

def get_name_without_extension(file_path):
    file_name = get_name(file_path)
    return os.path.splitext(file_name)[0]


