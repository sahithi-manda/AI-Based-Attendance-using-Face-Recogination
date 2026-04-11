import numpy as np

def face_locations(rgb_image):
    return [(50, 150, 150, 50)]

def face_encodings(rgb_image, known_face_locations=None):
    return [np.zeros(128)]
