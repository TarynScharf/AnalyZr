from enum import Enum


class ImageType(Enum):
    TL = 'TL'
    RL = 'RL'
    MASK = 'Mask'
    COLLAGE = 'Collage'
    CL = 'Cathodoluminescence'
    FI = 'Filter Image'


    def file_pattern(self):
        if self == ImageType.TL:
            return "TL"
        if self == ImageType.RL:
            return "RL"
        if self == ImageType.COLLAGE:
            return ""
        if self == ImageType.MASK:
            return "mask"