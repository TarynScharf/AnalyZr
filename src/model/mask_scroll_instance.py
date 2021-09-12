import json
import os

from src.model import json_data
from src.model.image_type import ImageType
from src.model.json_data import JsonData


class MaskScrollInstance:
    def __init__(self,view):
        self.pointer = -1
        self.mask_list = None
        self.source_files = None
        self.view = view


    def create_mask_list(self, folder_path):
        image_list = []
        for path, folder, files in os.walk(folder_path):
            for name in files:
                if os.path.splitext(name)[1].lower() != '.png':
                    continue
                image_path = os.path.join(folder_path, name)
                image_list.append(image_path)
        self.mask_list = image_list

    def create_source_file_dictionary(self,json_folder):
        source_images = {}
        for mask_path in self.mask_list:
            json_name = JsonData.get_json_file_name_from_path(ImageType.MASK, mask_path)
            region_id = JsonData.get_region_id_from_file_path(ImageType.MASK, mask_path)
            json_file_path = os.path.join(json_folder, json_name)
            try:
                with open(json_file_path, errors='ignore') as jsonFile:
                    data = json.load(jsonFile)
            except:
                error_message_text = f"File does not exist: {json_file_path}."
                self.view.open_error_message_popup_window(error_message_text)
                return False
            for region in data['regions']:
                if region['id'] == region_id:
                    if 'RL_Path' in region and 'TL_Path' in region:
                        rl_path = region['RL_Path']
                        tl_path = region['TL_Path']
                    else:
                        rl_path = ''
                        tl_path = ''
                    source_images[mask_path] = [rl_path, tl_path]
        self.source_files =  source_images

        return True

    def increment_pointer(self):
        if self.pointer >= len(self.mask_list)-1:
            self.pointer = 0
        else:
            self.pointer += 1


    def decrement_pointer(self):
        if self.pointer == 0:
            self.pointer = len(self.mask_list)-1
        else:
            self.pointer -= 1

    def get_current_mask_file_path(self):
            return self.mask_list[self.pointer]

