from src.model.drawing_objects.drawing_object import DrawingObject

class Spot(DrawingObject):
    def __init__(self, x0, y0, groupTag):
        super().__init__(groupTag)
        self.x0 = x0
        self.y0 = y0
        self.unique_tag = 'spot_'+self.unique_tag
        self.unique_text_tag = 'spot_'+self.unique_text_tag
        self.cl_texture = None
        self.notes = None

    def type(self):
        return "SPOT"


    @staticmethod
    def fromJSONData(region):
        x0 = region['points'][0]['x']
        y0 = region['points'][0]['y']
        group_tag = 'spot_'+region['id']

        spot = Spot(x0, y0, group_tag)
        if 'cl_texture' in region:
            cl_texture = region['cl_texture']
            spot.cl_texture = cl_texture
        if 'notes' in region:
            notes= region['notes']
            spot.notes = notes
        return spot

    def to_json_data(self):
        newRegion = {"id": self.group_tag, "type": "POINT", "tags": ["SPOT"],
                     "boundingBox": {"height": 5, "width": 5, "left": self.x0, "top": self.y0},
                     "points": [{"x": self.x0, "y": self.y0}],
                     "cl_texture": self.cl_texture,
                     "notes": self.notes}
        return newRegion