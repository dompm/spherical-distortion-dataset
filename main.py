import argparse

from spherical_distortion import generate_dataset_with_random_parameters, generate_dataset_from_metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Spherical distortion dataset generator.')
    parser.add_argument('--pano_dir', type=str, help='Directory of panoramas')
    parser.add_argument('--output_dir', type=str, help='Directory for the generated crops')
    parser.add_argument('--metadata_dir', type=str, help='Directory of json files with camera parameters. If not specified, camera parameters will be sampled randomly.')

    opt = parser.parse_args()

    if opt.metadata_dir:
        generate_dataset_from_metadata(panos_dir=opt.pano_dir,
                                        output_dir=opt.output_dir,
                                        metadata_dir=opt.metadata_dir)
    else:
        generate_dataset_with_random_parameters(panos_dir=opt.pano_dir,
                                                output_dir=opt.output_dir)