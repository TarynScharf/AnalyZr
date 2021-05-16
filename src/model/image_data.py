from src.model.drawing_objects.rectangle import Rectangle
from src.model.drawing_objects.scale import Scale
from src.model.drawing_objects.spot import Spot


class ImageData:
    def __init__(self, json_path,image_path):
        self.spots = []
        self.spot_areas = []

        self.unwanted_objects = []
        self.scale = None

        self.contours = []
        self.breaklines = []

        self.image_path = image_path
        self.json_path = json_path

    def get_image_name(self):
        return self.image_path.split('/')[-1]

    @staticmethod
    def fromJSONData(data,json_path):
        image_path = data['asset']['name']

        image_data = ImageData(json_path,image_path)

        spot_count = 0
        for region in data['regions']:
            if region['type'] == 'RECTANGLE':
                rectangle = Rectangle.fromJSONData(region)
                if rectangle.type == "DUPLICATE":
                    image_data.unwanted_objects.append(rectangle)
                if rectangle.type == "SPOT AREA":
                    image_data.spot_areas.append(rectangle)

            if region['type'] == 'POINT':
                spot = Spot.fromJSONData(region)
                image_data.spots.append(spot)
                spot_count += 1

            if region['tags'][0] == 'SCALE':
                scale = Scale.fromJSONData(region)
                image_data.scale = scale


        return image_data