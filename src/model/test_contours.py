import cv2
import numpy as np


# calculate direction vector
v1 = np.array([[1,0],[1,1]])
v1_norm = np.linalg.norm(v1,axis = 1)
print(f' v1_norm:\n {v1_norm}')

v2 = np.array([[0,1],[-1,1]])
v2_norm =np.linalg.norm(v2,axis = 1)
print(f' v2_norm:\n {v2_norm}')

v1_thing = np.array([[v1_norm[0],v1_norm[0]],[v1_norm[1],v1_norm[1]]])
v2_thing = np.array([[v2_norm[0],v2_norm[0]],[v2_norm[1],v2_norm[1]]])

v1_normalised = v1/v1_thing
print(f' v1_normalised:\n {v1_normalised}')

v2_normalised = v2 / v2_thing
print(f' v2_normalised:\n {v2_normalised}')

v3 = v1_normalised + v2_normalised
print(f' v3:\n {v3}')

# rotate by 90 degrees clockwise
bisection_vectors = np.flip(np.multiply(v3, np.array([-1, 1])), axis=1)
print(bisection_vectors)