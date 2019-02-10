import copy, json


class Key:
    __slots__ = [
        'x', 'y', 'width', 'height', 'x2', 'y2', 'width2', 'height2',
        'rotation_angle', 'rotation_x', 'rotation_y',
    ]


    def __init__(self):
        self.x = self.y = 0.0
        self.width = self.height = 1.0
        self.x2 = self.y2 = 0.0
        self.width2 = self.height2 = 0.0

        self.rotation_angle = 0.0
        self.rotation_x = self.rotation_y = 0.0


    def __eq__(self, other):
        return isinstance(other, Key) and self.__slots__ == other.__slots__


def deserialise(rows):
    # Initialize with defaults
    current, keys = Key(), []

    for row in rows:
        if isinstance(row, list):
            for key in row:
                if isinstance(key, str):
                    newKey = copy.copy(current)
                    keys.append(newKey)

                    # Set up for the next key
                    current.x += current.width
                    current.width = current.height = 1.0
                    current.x2 = current.y2 = current.width2 = current.height2 = 0.0
                else:
                    if 'r' in key:
                        current.rotation_angle = key['r']
                    if 'rx' in key:
                        current.rotation_x = key['rx']
                        current.x = current.y = 0
                    if 'ry' in key:
                        current.rotation_y = key['ry']
                        current.y = current.y = 0
                    if 'x' in key:
                        current.x += float(key['x'])
                    if 'y' in key:
                        current.y += float(key['y'])
                    if 'w' in key:
                        current.width = float(key['w'])
                    if 'h' in key:
                        current.height = float(key['h'])
                    if 'x2' in key:
                        current.x2 = float(key['x2'])
                    if 'y2' in key:
                        current.y2 = float(key['y2'])
                    if 'w2' in key:
                        current.width2 = float(key['w2'])
                        current.height2 = current.height
                    if 'h2' in key:
                        current.height2 = float(key['h2'])
                        current.width2 = current.width if current.width2 == 0.0 else current.width2
            # End of the row
            current.y += 1.0
        current.x = 0
    return keys
