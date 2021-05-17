from src.model.drawing_objects.drawing_object import DrawingObject


class Scale(DrawingObject):
    def __init__(self, x0, y0, x1, y1, group_tag):
        super().__init__(group_tag)
        self.x0 = min(x0,x1)
        self.y0 = min(y0,y1)
        self.x1 = max(x0,x1)
        self.y1 = max(y0,y1)
        self.real_world_distance = 30

    def type(self):
        return "SCALE"

    @staticmethod
    def fromJSONData(region):
        group_tag = region['id']
        x1 = region['points'][0]['x']
        y1 = region['points'][0]['y']
        x2 = region['points'][1]['x']
        y2 = region['points'][1]['y']

        return Scale(x1,y1,x2,y2,group_tag)

    def to_json_data(self):
        height = abs(self.x0 - self.x1)
        width = abs(self.y0 - self.y1)

        top = self.y0
        bottom = self.y1
        left = self.x0
        right = self.x1

        newRegion = {"id": self.unique_tag, "type": "SCALE", "tags": ["SCALE"],
                     "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                     "points": [{"x": self.x0, "y": self.y0},
                                {"x": self.x1, "y": self.y1}]}

        return newRegion

