from glob import glob
import numpy as np
from imageio import imread, imsave
from scipy.stats import cauchy, lognorm, norm, uniform
import json
from tqdm import tqdm
import os

from .spherical_distortion import crop_distortion

def generate_dataset_from_metadata(panos_dir, output_dir, metadata_dir):
    json_paths = glob(f"{metadata_dir}/*.json")

    for json_path in tqdm(json_paths):
        with open(json_path, 'r') as flhd:
            data = json.load(flhd)

        pano_name, crop_name, parameters = data

        pano_path = glob(f'{panos_dir}/**/{pano_name}*', recursive=True)[0]

        crop = crop_distortion(pano_path,
                                f=parameters['f_px'],
                                xi=parameters['spherical_distortion'],
                                H=parameters['height'],
                                W=parameters['width'],
                                az=parameters['yaw']*180/np.pi,
                                el=parameters['pitch']*180/np.pi,
                                roll=parameters['roll']*180/np.pi)

        imsave(f'{output_dir}/{crop_name}', crop)

def generate_dataset_with_random_parameters(panos_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    pano_paths = glob(f"{panos_dir}/*")

    aspect_ratios, ar_probabilities = zip(*(
        (1/1, 0.09), # Old cameras, Polaroids and Instagram
        (5/4, 0.01), # Large and medium format photography, 8x10 picture frames
        (4/3, 0.66), # Most point-and-shoots, Four-Thirds cameras, 
        (3/2, 0.20), # 35mm cameras, D-SLR
        (16/9, 0.04), # Cameras mimicking the 16:9 widescreen format
    ))

    for pano_path in tqdm(pano_paths):
        pano_name = pano_path.split('/')[-1][:-4]

        for i in range(7):
            crop_name = f'{pano_name}-{i}'
            
            # sampling of random camera parameters
            sensor_size = 24 # height of sensor (a 35mm sensor is 24mm x 36mm)

            aspect_ratio = np.asscalar(np.random.choice(aspect_ratios, p=ar_probabilities))
            height = 1024
            width = int(height * aspect_ratio)

            # 20% probability of a portait image
            if uniform.rvs() < 0.2:
                sensor_size = 36

                width, height = height, width

            focal_length = min(lognorm.rvs(s=0.8, loc=14, scale=16), 100)
            f_px = focal_length * width / 36

            yaw = uniform.rvs(loc=i/7*2*np.pi, scale=1/7*2*np.pi)

            roll = np.inf
            while abs(roll) > 0.75:
                if uniform.rvs() < 0.33:
                    roll = cauchy.rvs(scale=0.001)
                else:
                    roll = cauchy.rvs(scale=0.1)

            midpoint = norm.rvs(loc=0.523, scale=0.3)
            
            pitch = -np.arctan((midpoint - 0.5) / focal_length * sensor_size)

            if uniform.rvs() < 0.1:
                distortion = np.random.triangular(0,0,1)
            else:
                distortion = np.random.triangular(0,0.3,1)

            # crop generation
            try:
                crop = crop_distortion(pano_path, f=f_px, xi=distortion, H=height, W=width, az=yaw*180/np.pi, el=pitch*180/np.pi, roll=roll*180/np.pi)
            except ValueError:
                print(pano_path)
                continue

            # saving
            imsave(f'{output_dir}/{crop_name}.jpg', crop)
            with open(f'{output_dir}/{crop_name}.json', 'w+') as flhd:
                json.dump([pano_name, crop_name+'.jpg', {"yaw": yaw,
                                                    "pitch": pitch,
                                                    "roll": roll,
                                                    "vfov": None,
                                                    "focal_length_35mm_eq": focal_length,
                                                    "f_px": f_px,
                                                    "height": height,
                                                    "width": width,
                                                    "spherical_distortion": distortion,
                                                    "offset": None,
                                                    }], flhd)
