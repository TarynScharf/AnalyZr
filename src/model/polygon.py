class ContourPolygon:
    def __init__(self,groupTag, uniqueTag,coord_pairs = None):
        self.uniqueTag = uniqueTag
        self.groupTag = groupTag
        self.coord_ids = []
        self.type = "POLYGON"

        if coord_pairs == None:
            self.x_coords = []
            self.y_coords = []
        else:
            x,_y = zip(*coord_pairs)
            self.x_coords = list(x)
            self.y_coords = list(y)

    def add_vertex(self,x,y, id=None):
        self.x_coords.append(x)
        self.y_coords.append(y)
        self.coord_ids.append(id)

    def flatten_coordinates(self):
        #returns x0,y0,x1,y1....etc as required by tkinter for drawing a polygon
        coords_flattened=[]
        for x, y in zip(self.x_coords, self.y_coords):
            coords_flattened.append(x,y)
        return coords_flattened

    def paired_coordinates(self):
        return list(zip(self.x_coords, self.y_coords))

    def inverted_paired_coordinates(self):
        return list(zip(self.y_coords, self.x_coords))

    def size(self):
        #tells us how many vertices are in the polygon
        return len(self.x_coords)



