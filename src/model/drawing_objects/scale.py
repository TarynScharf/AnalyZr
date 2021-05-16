from src.model.drawing_objects.drawing_object import DrawingObject


class Scale(DrawingObject):
    def __init__(self, x0, y0, x1, y1, group_tag):
        super().__init__(group_tag)
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
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