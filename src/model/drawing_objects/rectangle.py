import uuid
from enum import Enum

from src.model.drawing_objects.drawing_object import DrawingObject

class RectangleType(Enum):
    SPOT_AREA = 'SPOT AREA'
    SPOT = 'SPOT'
    DUPLICATE = 'DUPLICATE'
    RL = 'RL'
    TL = 'TL'
    FI = 'FI'
    CL = 'CL'

class Rectangle(DrawingObject):
    def __init__(self, x0, y0, x1, y1, type, group_tag):
        super().__init__(group_tag)
        self.x0 = min(x0,x1)
        self.y0 = min(y0,y1)
        self.x1 = max(x0,x1)
        self.y1 = max(y0,y1)
        self.type = type

    def get_colour(self):
        if self.type == RectangleType.SPOT_AREA:
            return 'blue'
        else:
            return 'red'

    def get_height_and_width(self):
        height = abs(self.y0 - self.y1)
        width = abs(self.x0 - self.x1)

        return height,width

    @staticmethod
    def fromJSONData(region):
        type = RectangleType(region['tags'][0])
        x1 = region['points'][0]['x']
        y1 = region['points'][0]['y']
        x2 = region['points'][2]['x']
        y2 = region['points'][2]['y']
        group_tag = region['id']

        if type in [RectangleType.RL, RectangleType.TL, RectangleType.CL, RectangleType.FI]:
            return ImageRegion._from_json_data(region, type, x1, y1, x2, y2, group_tag)
        else:
            return Rectangle(x1, y1, x2, y2, type, group_tag)

    def to_json_data(self):
        height, width = self.get_height_and_width()

        top = self.y0
        bottom = self.y1
        left = self.x0
        right = self.x1

        newRegion = {"id": self.group_tag, "type": "RECTANGLE", "tags": [self.type.value],
                     "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                     "points": [{"x": left, "y": top}, {"x": right, "y": top}, {"x": right, "y": bottom},
                                {"x": left, "y": bottom}]}

        return newRegion

    def get_centroid(self):
        x = self.x0 + ((self.x1 - self.x0)/2)
        y = self.y0 + ((self.y1 - self.y0)/2)
        return x,y

    def translate_coordinates(self, delta_x, delta_y):
        self.x0 += delta_x
        self.y0 += delta_y
        self.x1 += delta_x
        self.y1 += delta_y

class ImageRegion(Rectangle):
    def __init__(self, x0, y0, x1, y1, type, group_tag, tl_path=None, rl_path=None, mask_path=None):
        super().__init__(x0, y0, x1, y1, type, group_tag)

        #for an image region, the group-tag corresponds to the region id

        self.tl_path = tl_path
        self.rl_path = rl_path
        self.mask_path = mask_path

    def to_json_data(self):
        data = super().to_json_data()

        if self.tl_path:
            data ["TL_Path"] = self.tl_path
        if self.rl_path:
            data["RL_Path"] = self.rl_path
        if self.mask_path:
            data["Mask_Path"] = self.mask_path
        return data

    @staticmethod
    def _from_json_data(region, type, x0, y0, x1, y1, group_tag):
        rl_path = region["RL_Path"] if "RL_Path" in region else None
        tl_path = region["TL_Path"] if "TL_Path" in region else None
        mask_path = region["Mask_Path"] if "Mask_Path" in region else None

        image_region = ImageRegion(x0, y0, x1, y1, type, group_tag, tl_path, rl_path, mask_path)
        return image_region
