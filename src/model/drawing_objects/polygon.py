import uuid
from enum import Enum
from src.model.drawing_objects.drawing_object import DrawingObject

class Polygon(DrawingObject):
    #This class is currently exclusively developed for displaying contour polygons that exist in json files derived from NON-COLLAGE images
    def __init__(self, points, group_tag):
        super().__init__(group_tag)
        self.coordinates= points
        self.type = 'POLYGON'

    @staticmethod
    def fromJSONData(region):
        polygon_points = []
        for point in region['points']:
            polygon_points.append(point['x'])
            polygon_points.append(point['y'])

        group_tag = region['id']

        return Polygon(polygon_points, group_tag)