import os

from src.model.drawing_objects.rectangle import Rectangle, RectangleType
from src.model.drawing_objects.scale import Scale
from src.model.drawing_objects.spot import Spot
from src.model.image_type import ImageType


class ImageData:
    def __init__(self, json_path,data_capture_image_path,data_capture_image_type=None, data_capture_image_name = None,rl_path=None, tl_path = None, mask_path = None):
        self.spots = []
        self.spot_areas = []

        self.unwanted_objects = []
        self.scale = None

        self.contours = []
        self.breaklines = []

        self.data_capture_image_type = data_capture_image_type
        self.data_capture_image_name = data_capture_image_name

        self.data_capture_image_path = data_capture_image_path
        self.json_path = json_path

        self.rl_path = rl_path
        self.tl_path = tl_path
        self.mask_path = mask_path

    def get_image_name(self):
        return self.data_capture_image_path.split('/')[-1]




    @staticmethod
    def fromJSONData(data,json_path):
        data_capture_image_path = data['asset']['name']

        image_data = ImageData(json_path,data_capture_image_path)

        spot_count = 0
        for region in data['regions']:
            if region['type'] == 'RECTANGLE':
                rectangle = Rectangle.fromJSONData(region)
                if rectangle.rectangle_type == RectangleType.DUPLICATE:
                    image_data.unwanted_objects.append(rectangle)
                if rectangle.rectangle_type in[RectangleType.SPOT_AREA, RectangleType.SPOT]:
                    image_data.spot_areas.append(rectangle)

            if region['type'] == 'POINT':
                spot = Spot.fromJSONData(region)
                image_data.spots.append(spot)
                spot_count += 1

            if region['tags'][0] == 'SCALE':
                scale = Scale.fromJSONData(region)
                image_data.scale = scale


        return image_data
