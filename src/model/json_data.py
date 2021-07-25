import json
import os
import re

from src.model import FileUtils
from src.model.drawing_objects.rectangle import Rectangle, RectangleType, ImageRegion
from src.model.drawing_objects.scale import Scale
from src.model.drawing_objects.spot import Spot
from src.model.image_type import ImageType

'''
    Format of image file names that this supports:
    GSWA collage image: sampleID_anything
    reflected light image: sampleid_anything_RL(_regionid)
    transmitted light image: sampleid_anything_TL(_regionid)
    mask image: sampleid_anything_mask(_regionid)
    json file: sampleid_anything
    
    legacy file format: 
    data capture image: sampleid_spots_pagenumber
    json file: sampleid_spots_pagenumber
    mask image: sampleid_spots_pagenumber_RL_rlregionid
    reflected light image: sampleid_spots_pagenumber_TL_tlregionid
    transmitted light image: sampleid_spots_pagenumber_TL_rlregionid
    
'''

class JsonData:
    def __init__(self,data_capture_image_path,data_capture_image_type,image_width,image_height):
        self.data_capture_image_path = data_capture_image_path
        self.data_capture_image_type = data_capture_image_type
        self.scale = None
        self.spot_areas = []
        self.spots = []
        self.image_regions = []
        self.unwanted_objects  = []

        self.image_width = image_width
        self.image_height = image_height

        self.json_file_path = None
        self.rl_path = None
        self.tl_path = None
        self.mask_path = None

    def add_first_image_region(self):
        if self.data_capture_image_type not in [ImageType.RL, ImageType.TL, ImageType.CL, ImageType.FI]:
            raise ValueError('Unrecognised image type')
        x0 = 0
        y0 = 0
        x1 = self.image_width
        y1 = self.image_height

        group_tag = hash(self.data_capture_image_path)
        region = ImageRegion(x0, y0, x1, y1, self.data_capture_image_type, group_tag)
        self.image_regions.append(region)

    def to_json_data(self):
        regions = []

        if self.scale:
            regions.append(self.scale.to_json_data())
        for spot_area in self.spot_areas:
            regions.append(spot_area.to_json_data())
        for spot in self.spots:
            regions.append(spot.to_json_data())
        for unwanted_object in self.unwanted_objects:
            regions.append(unwanted_object.to_json_data())
        for image_region in self.image_regions:
            regions.append(image_region.to_json_data())

        data = {
            "asset": {
                "format": FileUtils.get_extension(self.data_capture_image_path),
                "id": hash(self.data_capture_image_path),
                "name": FileUtils.get_name(self.data_capture_image_path),
                "path": self.data_capture_image_path,
                "data capture image type": ImageType(self.data_capture_image_type.value).name,
                "size": {
                    "width": self.image_width,
                    "height": self.image_height
                },
            },
            "regions": regions
        }
        return data


    @staticmethod
    def from_json_data(data):
        data_capture_image_path = data['asset']['path']
        width = data['asset']['size']['width']
        height = data['asset']['size']['height']
        if 'data capture image type' in data['asset']:
            image_type = data['asset']['data capture image type']
        else:
            image_type = ImageType.COLLAGE #legacy
        json_data = JsonData(data_capture_image_path,image_type,width, height)

        for region in data['regions']:
            if region['tags'][0] == 'SCALE':
                scale = Scale.fromJSONData(region)
                json_data.scale = scale

            if region['type'] == 'RECTANGLE':
                rectangle = Rectangle.fromJSONData(region)
                if rectangle.type == RectangleType.DUPLICATE:
                    json_data.unwanted_objects.append(rectangle)
                elif rectangle.type == RectangleType.SPOT_AREA:
                    json_data.spot_areas.append(rectangle)
                elif rectangle.type == RectangleType.SPOT:
                    # Reading legacy spots that were stored as rectangles
                    x,y = rectangle.get_centroid()
                    spot = Spot(x,y,rectangle.group_tag)
                    json_data.spots.append(spot)
                elif rectangle.type in [RectangleType.RL, RectangleType.TL, RectangleType.CL, RectangleType.FI]:
                    json_data.image_regions.append(rectangle)
                else:
                    pass

            if region['type'] == 'POINT':
                spot = Spot.fromJSONData(region)
                json_data.spots.append(spot)

        return json_data

    def get_data_capture_image_name(self):
        return FileUtils.get_name(self.data_capture_image_path)

    def get_image_region(self, region_id):
        if region_id is None:
            return self.image_regions[0]

        for region in self.image_regions:
            if region.group_tag == region_id:
                return region

    def save_changes_to_region(self, region_id, region_object, json_file_path):
        with open(json_file_path, errors='ignore') as json_file:
            data = json.load(json_file)

        for region_data in data['regions']:
            if region_data['id'] == region_id:
                old_region_data = region_data

        new_region_data = region_object.to_json_data()
        data['regions'].remove(old_region_data)
        data['regions'].append(new_region_data)

        with open(json_file_path, 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)

    @staticmethod
    def get_json_file_name_from_path(image_type, image_path):
        image_name = FileUtils.get_name_without_extension(image_path)

        if image_type == ImageType.COLLAGE:
            unique_name = FileUtils.get_name_without_extension(image_name)
            return unique_name+ ".json"

        if image_type in [ImageType.TL, ImageType.RL,  ImageType.MASK]:
            pattern = "_"+image_type.file_pattern()
            result = re.search(pattern, image_name, re.IGNORECASE)

            if result is not None:
                index = result.start()
                unique_name =image_name[:index]
            elif image_type == ImageType.MASK:
                #legacy format
                unique_name = '_'.join(image_name.split('_')[:3])
            else:
                raise ValueError(f'File name {image_name} is not of the correct form. No {pattern} found.')

            return unique_name+ ".json"

        raise ValueError(f'Unsupported filename for image type: {image_type.value}.')

    @staticmethod
    def get_region_id_from_file_path(image_type, image_path):
        image_name = FileUtils.get_name_without_extension(image_path)
        if image_type in [ImageType.TL, ImageType.RL,  ImageType.MASK]:
            pattern = "_"+image_type.file_pattern()

            result = re.search(pattern, image_name, re.IGNORECASE)
            if result is not None:
                index = result.start()+1
                region_id =image_name[index+len(pattern):]
                if region_id == '':
                    #application when not using collage images
                    return None
            elif image_type == ImageType.MASK:
                #legacy format
                region_id = '_'.join(image_name.split('_')[4:])
            else:
                raise ValueError(f'File name {image_name} is not of the correct form. No {pattern} found.')

            return region_id

    @staticmethod
    def get_sample_id_from_file_path(path):
        file_name = FileUtils.get_name_without_extension(path)
        sampleid = file_name.split('_')[0]
        return sampleid


    def save_all(self):
        json_file_name = JsonData.get_json_file_name_from_path(self.data_capture_image_type, self.data_capture_image_path)
        folder = FileUtils.get_folder(self.data_capture_image_path)
        data = self.to_json_data()
        with open(os.path.join(folder, json_file_name), 'w', errors='ignore') as new_json:
            json.dump(data, new_json, indent=4)

    @staticmethod
    def load_all(json_file_path):
        with open(json_file_path, errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        return JsonData.from_json_data(data)



