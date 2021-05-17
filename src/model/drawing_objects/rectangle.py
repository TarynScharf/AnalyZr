import uuid
from enum import Enum

from src.model.drawing_objects.drawing_object import DrawingObject

class RectangleType(Enum):
    SPOT_AREA =  'SPOT AREA'
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

    @staticmethod
    def fromJSONData(region):
        x1 = region['points'][0]['x']
        y1 = region['points'][0]['y']
        x2 = region['points'][1]['x']
        y2 = region['points'][2]['y']
        type = RectangleType(region['tags'][0])
        group_tag = region['id']
        return Rectangle(x1, y1, x2, y2, type, group_tag)

    def get_height_and_width(self):
        height = abs(self.y0 - self.y1)
        width = abs(self.x0 - self.x1)

        return height,width

    def to_json_data(self):
        height, width = self.get_height_and_width()

        top = self.y0
        bottom = self.y1
        left = self.x0
        right = self.x1


        newRegion = {"id": self.unique_tag, "type": "RECTANGLE", "tags": [self.type.value],
                     "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                     "points": [{"x": left, "y": top}, {"x": right, "y": top}, {"x": right, "y": bottom},
                                {"x": left, "y": bottom}]}

        return newRegion