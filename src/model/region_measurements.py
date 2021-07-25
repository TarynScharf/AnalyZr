import math
import numpy as np

class RegionMeasurement():
    def __init__(self,
        sampleid,
        image_id,
        grain_number,
        grain_centroid,
        area,
        equivalent_diameter,
        perimeter,
        minor_axis_length,
        major_axis_length,
        solidity,
        convex_area,
        minFeret,
        maxFeret,
        contour,
        image_dimensions,
        mask_image
    ):
        self.sampleid = sampleid
        self.image_id = image_id # unique code coming from VOTT, per image
        self.grain_number = grain_number
        self.grain_centroid =grain_centroid # centroid of grain
        self.grain_spots = ''
        self.area= area
        self.equivalent_diameter = equivalent_diameter
        self.perimeter = perimeter
        self.minor_axis_length = minor_axis_length
        self.major_axis_length = major_axis_length
        self.solidity = solidity
        self.convex_area = convex_area
        self.minFeret = minFeret
        self.maxFeret = maxFeret
        self.contour =contour
        self.image_region =image_dimensions
        self.mask_image =mask_image

        self.formFactor = (4 * math.pi * area) / (perimeter ** 2)
        self.roundness = (4 * area) / (math.pi * (major_axis_length ** 2))
        self.compactness = (math.sqrt((4 / math.pi) * area) / major_axis_length)
        self.aspectRatio = major_axis_length / minor_axis_length

    def as_list(self):
        contour = ",".join([f'({x},{y})'for x,y in np.squeeze(self.contour)])
        image_dimensions = f'{int(round(self.image_region.y0))},{int(round(self.image_region.x0))},{int(round(self.image_region.y1))},{int(round(self.image_region.x1))}'
        def round_decimals_for_display(value, decimal=2):
            return str(round(value,decimal))

        return [self.sampleid,
                self.image_id,
                self.grain_number,
                self.grain_spots,
                round_decimals_for_display(self.grain_centroid[0]),
                round_decimals_for_display(self.grain_centroid[1]),
                round_decimals_for_display(self.area),
                round_decimals_for_display(self.equivalent_diameter),
                round_decimals_for_display(self.perimeter),
                round_decimals_for_display(self.minor_axis_length),
                round_decimals_for_display(self.major_axis_length),
                round_decimals_for_display(self.solidity),
                round_decimals_for_display(self.convex_area),
                round_decimals_for_display(self.formFactor),
                round_decimals_for_display(self.roundness),
                round_decimals_for_display(self.compactness),
                round_decimals_for_display(self.aspectRatio),
                round_decimals_for_display(self.minFeret),
                round_decimals_for_display(self.maxFeret),
                image_dimensions,
                self.mask_image,
                contour
                ]

    @staticmethod
    def get_headers():
        return ['sample_id',
                'image_id',
                'grain_number',
                'analytical_spot',
                'grain_centroid_x',
                'grain_centroid_y',
                'area',
                'equivalent_diameter',
                'perimeter',
                'minor_axis_length',
                'major_axis_length',
                'solidity',
                'convex_area',
                'formFactor',
                'roundness',
                'compactness',
                'aspect_ratio',
                'min_feret',
                'max_feret',
                'image_dimensions',
                'mask_image',
                'contour'
                ]
    @staticmethod
    def get_database_headers():
        return ['sampleid',
                'image_id',
                'grain_number',
                'grain_centroid',
                'grain_spots',
                'area',
                'equivalent_diameter',
                'perimeter',
                'minor_axis_length',
                'major_axis_length',
                'solidity',
                'convex_area',
                'formFactor',
                'roundness',
                'compactness',
                'aspectRatio',
                'minFeret',
                'maxFeret',
                'contour',
                'image_dimensions',
                'mask_image']

    def get_database_row(self):

        def quote(value):
            return f"'{value}'"

        return [self.sampleid,
                quote(self.image_id),
                str(self.grain_number),
                quote(self.grain_centroid),
                quote(self.grain_spots),
                str(self.area),
                str(self.equivalent_diameter),
                str(self.perimeter),
                str(self.minor_axis_length),
                str(self.major_axis_length),
                str(self.solidity),
                str(self.convex_area),
                str(self.formFactor),
                str(self.roundness),
                str(self.compactness),
                str(self.aspectRatio),
                str(self.minFeret),
                str(self.maxFeret),
                quote(self.contour),
                quote(self.image_region),
                quote(self.mask_image)
                ]