import json
import numpy as np
from scipy import interpolate

with open('perceptual_measure/perceptual_planes/pitch_plane.json') as flhd:
    pitch_plane = json.load(flhd)

with open('perceptual_measure/perceptual_planes/roll_plane.json') as flhd:
    roll_plane = json.load(flhd)
    roll_plane['value'] = [value * 180 / np.pi for value in roll_plane['value']]
    roll_plane['error'] = [error * 180 / np.pi for error in roll_plane['error']]

with open('perceptual_measure/perceptual_planes/fov_plane.json') as flhd:
    hfov_plane = json.load(flhd)
    hfov_plane['value'] = [value * 180 / np.pi for value in hfov_plane['value']]
    hfov_plane['error'] = [error * 180 / np.pi for error in hfov_plane['error']]
    
with open('perceptual_measure/perceptual_planes/distortion_plane.json') as flhd:
    distortion_plane = json.load(flhd)

planes = {'pitch': pitch_plane, 'roll': roll_plane, 'hfov': hfov_plane, 'distortion': distortion_plane}

def _get_perceptual_measure(value, error, parameter_name):
    plane = planes[parameter_name]

    value_inter = np.array(plane['value'])
    error_inter = np.array(plane['error'])
    perception_inter = np.array(plane['perception']) * 50 + 50

    perceptual_measure = interpolate.griddata((error_inter, value_inter), perception_inter, (error, value))

    return np.round(np.clip(perceptual_measure, 50, 100), 2)

def pitch_perceptual_measure(value, error):
    """
    Perceptual measure for the midpoint pitch in image unit (-0.5 at the bottom of the image, 0.5 at the top)

    value: ground truth pitch
    error: error on the estimated pitch (ground truth - estimated)
    """

    return _get_perceptual_measure(value, error, 'pitch')

def roll_perceptual_measure(value, error):
    """
    Perceptual measure for the roll in degrees

    value: ground truth roll
    error: error on the estimated roll (ground truth - estimated)
    """

    return _get_perceptual_measure(value, error, 'roll')

def hfov_perceptual_measure(value, error):
    """
    Perceptual measure for the horizontal effective field of view in degrees

    value: ground truth hfov
    error: error on the estimated hfov (ground truth - estimated)
    """
    return _get_perceptual_measure(value, error, 'hfov')

def distortion_perceptual_measure(value, error):
    """
    Perceptual measure for the distortion (xi) as defined in the spherical model

    value: ground truth distortion
    error: error on the estimated distortion (ground truth - estimated)
    """
    return _get_perceptual_measure(value, error, 'distortion')