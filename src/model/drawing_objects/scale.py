import math

from src.model.drawing_objects.drawing_object import DrawingObject


class Scale(DrawingObject):
    def __init__(self, x0, y0, x1, y1, group_tag, real_world_distance = None):
        super().__init__(group_tag)
        self.x0 = min(x0,x1)
        self.y0 = min(y0,y1)
        self.x1 = max(x0,x1)
        self.y1 = max(y0,y1)
        if real_world_distance == None:
            self.real_world_distance = 100
        else:
            self.real_world_distance = float(real_world_distance)

    def type(self):
        return "SCALE"

    @staticmethod
    def fromJSONData(region):
        real_world_distance = None
        group_tag = region['id']
        x1 = region['points'][0]['x']
        y1 = region['points'][0]['y']
        x2 = region['points'][1]['x']
        y2 = region['points'][1]['y']
        if "realWorldDistance" in region:
            real_world_distance = region['realWorldDistance']

        return Scale(x1,y1,x2,y2,group_tag,real_world_distance)

    def to_json_data(self):
        height = abs(self.x0 - self.x1)
        width = abs(self.y0 - self.y1)

        top = self.y0
        bottom = self.y1
        left = self.x0
        right = self.x1

        newRegion = {"id": self.group_tag, "type": "SCALE", "tags": ["SCALE"],"realWorldDistance":self.real_world_distance,
                     "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                     "points": [{"x": self.x0, "y": self.y0},
                                {"x": self.x1, "y": self.y1}]}

        return newRegion

    def get_length(self):
        delta_x = abs(self.x0-self.x1)
        delta_y = abs(self.y0-self.y1)
        distance = math.hypot(delta_x, delta_y)
        return distance

