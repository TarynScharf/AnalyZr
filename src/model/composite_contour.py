class CompositeContour:
    def __init__(self, original_points, index):
        self.original_points = original_points
        self.reconstructed_points = None
        self.coefficients = None
        self.cumulative_distance = None
        self.curvature_values = None
        self.max_curvature_values = None
        self.max_curvature_coordinates = None
        self.keep_contour:bool = True
        self.index = index
        self.has_parent = None
        self.locus = None
        self.max_bisectors = None

