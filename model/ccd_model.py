

class CCD():
    def __init__(self, type) -> None:
        self.type = type
        if type == 'IMX477':
            self.photo_size = (8112, 3040)
            self.image_size = (4056, 3040)
        else:
            raise Exception("Unidentified CCD type.")

