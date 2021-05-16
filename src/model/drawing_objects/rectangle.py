import uuid

from src.model.drawing_objects.drawing_object import DrawingObject

class Rectangle(DrawingObject):
    def __init__(self, x0, y0, x1, y1, type, group_tag):
        super().__init__(group_tag)
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.type = type

    def get_colour(self):
        if type == "SPOT AREA":
            return 'blue'
        else:
            return 'red'

    @staticmethod
    def fromJSONData(region):
        x1 = region['points'][0]['x']
        y1 = region['points'][0]['y']
        x2 = region['points'][1]['x']
        y2 = region['points'][2]['y']
        type = region['tags'][0]
        group_tag = region['id']
        return Rectangle(x1, y1, x2, y2, type, group_tag)