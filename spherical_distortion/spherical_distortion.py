import sys
import os
import numpy as np
from PIL import Image, ImageDraw
import imageio
import math as m
import cmath as cm
import time, glob
from scipy.ndimage.interpolation import zoom
import random
import pdb
from numpy.lib.scimath import sqrt as csqrt
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.stats import cauchy, lognorm, norm, uniform

from .my_interpol import interp2linear

def deg2rad(deg): # convert degrees to radians
    return deg*m.pi/180

def getRotationMat(roll, pitch, yaw): # compute the rotation matrix given 3 angles: roll, pitch and yaw

    rx = np.array([1., 0., 0., 0., np.cos(deg2rad(roll)), -np.sin(deg2rad(roll)), 0., np.sin(deg2rad(roll)), np.cos(deg2rad(roll))]).reshape((3, 3))
    ry = np.array([np.cos(deg2rad(pitch)), 0., np.sin(deg2rad(pitch)), 0., 1., 0., -np.sin(deg2rad(pitch)), 0., np.cos(deg2rad(pitch))]).reshape((3, 3))
    rz = np.array([np.cos(deg2rad(yaw)), -np.sin(deg2rad(yaw)), 0., np.sin(deg2rad(yaw)), np.cos(deg2rad(yaw)), 0., 0., 0., 1.]).reshape((3, 3))

    return np.matmul(rz, np.matmul(ry, rx))

def minfocal( u0,v0,xi,xref=1,yref=1): # compute the minimum focal for the image to be catadioptric given xi

    fmin = np.sqrt(-(1-xi*xi)*((xref-u0)*(xref-u0) + (yref-v0)*(yref-v0)))

    return fmin * 1.0001

def diskradius(xi, f): # compute the disk radius when the image is catadioptric
    return np.sqrt(-(f*f)/(1-xi*xi))

def crop_distortion(image360_path, f, xi, H, W, az, el, roll):

    u0 = W / 2.
    v0 = H / 2.

    grid_x, grid_y = np.meshgrid(list(range(W)), list(range(H)))

    if isinstance(image360_path, str):
        image360 = imageio.imread(image360_path) #.astype('float32') / 255.
    else:
        image360 = image360_path.copy()

    ImPano_W = np.shape(image360)[1]
    ImPano_H = np.shape(image360)[0]
    x_ref = 1
    y_ref = 1

    fmin = minfocal(u0, v0, xi, x_ref, y_ref) # compute minimal focal length for the image to ve catadioptric with given xi

    # 1. Projection on the camera plane

    X_Cam = np.divide(grid_x - u0, f)
    Y_Cam = -np.divide(grid_y - v0, f)

    # 2. Projection on the sphere

    AuxVal = np.multiply(X_Cam, X_Cam) + np.multiply(Y_Cam, Y_Cam)

    alpha_cam = np.real(xi + csqrt(1 + np.multiply((1 - xi * xi), AuxVal)))

    alpha_div = AuxVal + 1

    alpha_cam_div = np.divide(alpha_cam, alpha_div)

    X_Sph = np.multiply(X_Cam, alpha_cam_div)
    Y_Sph = np.multiply(Y_Cam, alpha_cam_div)
    Z_Sph = alpha_cam_div - xi

    # 3. Rotation of the sphere

    coords = np.vstack((X_Sph.ravel(), Y_Sph.ravel(), Z_Sph.ravel()))
    rot_el = np.array([1., 0., 0., 0., np.cos(deg2rad(el)), -np.sin(deg2rad(el)), 0., np.sin(deg2rad(el)), np.cos(deg2rad(el))]).reshape((3, 3))
    rot_az = np.array([np.cos(deg2rad(az)), 0., np.sin(deg2rad(az)), 0., 1., 0., -np.sin(deg2rad(az)), 0., np.cos(deg2rad(az))]).reshape((3, 3))
    rot_roll = np.array([np.cos(deg2rad(roll)), -np.sin(deg2rad(roll)), 0., np.sin(deg2rad(roll)), np.cos(deg2rad(roll)), 0., 0., 0., 1.]).reshape((3, 3))
    sph = rot_roll.dot(rot_el.dot(coords))
    sph = rot_az.dot(sph)

    sph = sph.reshape((3, H, W)).transpose((1,2,0))
    X_Sph, Y_Sph, Z_Sph = sph[:,:,0], sph[:,:,1], sph[:,:,2]

    # 4. cart 2 sph
    ntheta = np.arctan2(X_Sph, Z_Sph)
    nphi = np.arctan2(Y_Sph, np.sqrt(Z_Sph**2 + X_Sph**2))

    pi = m.pi

    # 5. Sphere to pano
    min_theta = -pi
    max_theta = pi
    min_phi = -pi / 2.
    max_phi = pi / 2.

    min_x = 0
    max_x = ImPano_W - 1.0
    min_y = 0
    max_y = ImPano_H - 1.0

    ## for x
    a = (max_theta - min_theta) / (max_x - min_x)
    b = max_theta - a * max_x  # from y=ax+b %% -a;
    nx = (1. / a)* (ntheta - b)

    ## for y
    a = (min_phi - max_phi) / (max_y - min_y)
    b = max_phi - a * min_y  # from y=ax+b %% -a;
    ny = (1. / a)* (nphi - b)

    # 6. Final step interpolation and mapping

    im = np.array(interp2linear(image360, nx, ny), dtype=np.uint8)

    if f < fmin:  # if it is a catadioptric image, apply mask and a disk in the middle
        r = diskradius(xi, f)
        DIM = im.shape
        ci = (np.round(DIM[0]/2), np.round(DIM[1]/2))
        xx, yy = np.meshgrid(list(range(DIM[0])) - ci[0], list(range(DIM[1])) - ci[1])
        mask = np.double((np.multiply(xx,xx) + np.multiply(yy,yy)) < r*r)
        mask_3channel = np.stack([mask, mask, mask], axis=-1).transpose((1,0,2))
        im = np.array(np.multiply(im, mask_3channel), dtype=np.uint8)

    return im

def get_horizon_line(W, H, f, xi, roll, el, number_of_points = 1000, el_first=True):
    u0 = W / 2
    v0 = H / 2

    X_Cam = np.linspace(-W, W, 1000) / f
    # X_Cam = np.array([0])

    omega = (xi + np.sqrt(1 + (1 - xi**2) * X_Cam**2)) / (X_Cam**2 + 1)

    X_Sph = X_Cam * omega
    Y_Sph = np.zeros(X_Sph.shape)
    Z_Sph = omega - xi

    coords = np.vstack((X_Sph.ravel(), Y_Sph.ravel(), Z_Sph.ravel()))
    rot_el = np.array([1., 0., 0., 0., np.cos(np.deg2rad(el)), -np.sin(np.deg2rad(el)), 0., np.sin(np.deg2rad(el)), np.cos(np.deg2rad(el))]).reshape((3, 3))
    rot_roll = np.array([np.cos(np.deg2rad(roll)), -np.sin(np.deg2rad(roll)), 0., np.sin(np.deg2rad(roll)), np.cos(np.deg2rad(roll)), 0., 0., 0., 1.]).reshape((3, 3))
    if el_first:
        sph = rot_roll.dot(rot_el.dot(coords))
    else:
        sph = rot_el.dot(rot_roll.dot(coords))

    sph = sph.reshape((3, 1, 1000)).transpose((1,2,0))

    X_Sph, Y_Sph, Z_Sph = sph[:,:,0], sph[:,:,1], sph[:,:,2]

    x = X_Sph * f / (xi * np.sqrt(X_Sph**2 + Y_Sph**2 + Z_Sph**2) + Z_Sph) + u0
    y = Y_Sph * f / (xi * np.sqrt(X_Sph**2 + Y_Sph**2 + Z_Sph**2) + Z_Sph) + v0

    f = interp1d(x.flatten(), y.flatten())

    x_horizon = np.linspace(0, W, number_of_points)
    y_horizon = f(x_horizon)

    x_midpoint = u0
    y_midpoint = f(x_midpoint)

    return x_horizon, y_horizon, x_midpoint, y_midpoint

def apply_distortion(crop_path, f, xi):
    # Seems like there is a sign error somewhere
    if isinstance(crop_path, str):
        crop = imageio.imread(crop_path) #.astype('float32') / 255.
    else:
        crop = crop_path.copy()

    H, W = crop.shape[0], crop.shape[1]
    u0 = W / 2.
    v0 = H / 2.

    grid_x, grid_y = np.meshgrid(list(range(W)), list(range(H)))

    X_Cam = np.divide(grid_x - u0, f)
    Y_Cam = -np.divide(grid_y - v0, f)

    AuxVal = np.multiply(X_Cam, X_Cam) + np.multiply(Y_Cam, Y_Cam)

    alpha_cam = np.real(xi + csqrt(1 + np.multiply((1 - xi * xi), AuxVal)))

    alpha_div = AuxVal + 1

    alpha_cam_div = np.divide(alpha_cam, alpha_div)

    X_Sph = np.multiply(X_Cam, alpha_cam_div)
    Y_Sph = np.multiply(Y_Cam, alpha_cam_div)
    Z_Sph = alpha_cam_div - xi

    X_d = X_Sph*f/Z_Sph + u0
    Y_d = Y_Sph*f/Z_Sph + v0

    im = np.array(interp2linear(crop, X_d, Y_d), dtype=np.uint8)

    return im, X_d, Y_d