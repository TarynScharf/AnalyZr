import math


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
        self.grainspot = ''
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
        self.image_dimensions =image_dimensions
        self.mask_image =mask_image

        self.formFactor = (4 * math.pi * area) / (perimeter ** 2),
        self.roundness = (4 * area) / (math.pi * (major_axis_length ** 2)),
        self.compactness = (math.sqrt((4 / math.pi) * area) / major_axis_length),
        self.aspectRatio = major_axis_length / minor_axis_length

    def as_list(self):
        return [self.sampleid,
                self.image_id,
                self.grain_number,
                self.grain_centroid,
                self.grainspot,
                self.area,
                self.equivalent_diameter,
                self.perimeter,
                self.minor_axis_length,
                self.major_axis_length,
                self.solidity,
                self.convex_area,
                self.formFactor,
                self.roundness,
                self.compactness,
                self.aspectRatio,
                self.minFeret,
                self.maxFeret,
                self.contour,
                self.image_dimensions,
                self.mask_image
                ]

    @staticmethod
    def get_headers():
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
                'mask_image'
                ]