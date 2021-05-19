import uuid

from src.model.drawing_objects.drawing_object import DrawingObject


class Contour(DrawingObject):
    def __init__(self,groupTag, coord_pairs = None):
        super().__init__(groupTag)
        self.coord_ids = []
        self.type = "POLYGON"

        if coord_pairs is None:
            self.x_coords = []
            self.y_coords = []
        else:
            x,y = zip(*coord_pairs)
            self.x_coords = list(x)
            self.y_coords = list(y)

    def add_vertex(self,x,y):
        self.x_coords.append(x)
        self.y_coords.append(y)
        self.coord_ids.append('p_' + str(uuid.uuid4()))

    def flatten_coordinates(self):
        #returns x0,y0,x1,y1....etc as required by tkinter for drawing a polygon
        coords_flattened=[]
        for x, y in zip(self.x_coords, self.y_coords):
            coords_flattened.append(x)
            coords_flattened.append(y)
        return coords_flattened

    def paired_coordinates(self):
        return list(zip(self.x_coords, self.y_coords))

    def inverted_paired_coordinates(self):
        return list(zip(self.y_coords, self.x_coords))

    def size(self):
        #tells us how many vertices are in the polygon
        return len(self.x_coords)



