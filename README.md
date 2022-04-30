# A Deep Perceptual Measure for Lens and Camera Calibration

This repository contains the code to generate the dataset and the perceptual measure from our paper:

> **A Deep Perceptual Measure for Lens and Camera Calibration**  
> Yannick Hold-Geoffroy¹ , Dominique Piché-Meunier³ , Kalyan Sunkavalli¹ , Jean-Charles Bazin², François Rameau², and Jean-François Lalonde³  
> Adobe¹ , KAIST² , Université Laval²

## Dataset
### Usage

To generate crops with randomly sampled camera parameters, run:

```
python main.py --pano_dir=<PANOS_ROOT> --output_dir=<OUTPUT_DIR>
```

In our paper, we use the purchasable panorama dataset [360Cities](https://www.360cities.net/) to generate crops. If you have access to the panoramas, you can generate our dataset by downloading the [crops metadata](https://drive.google.com/file/d/1Wy_3KdZuqzd6ZCARpZTa3k10BT7lSLOG/view?usp=sharing) and running

```
python main.py --pano_dir=<360CITIES_ROOT> --output_dir=<OUTPUT_DIR> --metadata_dir=360cities_metadata
```

Otherwise, we provide an open source version of the dataset based on [PolyHaven](https://polyhaven.com/hdris). The dataset can be downloaded [here](https://drive.google.com/file/d/1qR5kUBLlbjzREEHfSqTGzEOUO4z64rsP/view?usp=sharing). To regenerate the crops from the (tonemapped) panoramas, download the [crops metadata](https://drive.google.com/file/d/1v7johUDARrr4bAChHd-MuAavqKGpI9Vq/view?usp=sharing) and run:

```
python main.py --pano_dir=<POLYHAVEN_ROOT> --output_dir=<OUTPUT_DIR> --metadata_dir=polyhaven_metadata
```

### Examples

Here are some samples from the [PolyHaven dataset](https://drive.google.com/file/d/1qR5kUBLlbjzREEHfSqTGzEOUO4z64rsP/view?usp=sharing).

| ![adams_place_bridge-0](https://i.imgur.com/5gZnX6W.jpg) | ![aviation_museum-1](https://i.imgur.com/Gy74ILo.jpg) | ![arboretum-1](https://i.imgur.com/PJJ3s8k.jpg)      | ![aristea_wreck-0](https://i.imgur.com/d0cNr7t.jpg)     |
| -------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------- |
| ![autumn_forest_04-6](https://i.imgur.com/05vRj1A.jpg)   | ![ballroom-5](https://i.imgur.com/syIkSym.jpg)        | ![bell_park_pier-2](https://i.imgur.com/C5l4gvO.jpg) | ![blue_grotto-6](https://i.imgur.com/mQZeusv.jpg)       |
| ![boiler_room-3](https://i.imgur.com/e13V21f.jpg)        | ![bush_restaurant-5](https://i.imgur.com/WILYc1Q.jpg) | ![cannon-1](https://i.imgur.com/rBe3Mhi.jpg)         | ![carpentry_shop_02-0](https://i.imgur.com/K4PLmSz.jpg) |
| ![cambridge-2](https://i.imgur.com/CP58iQl.jpg)          | ![canary_wharf-3](https://i.imgur.com/dHXd2ru.jpg)    | ![cayley_lookout-0](https://i.imgur.com/zKsOplZ.jpg) | ![colosseum-2](https://i.imgur.com/3pkF2Og.jpg)         |
| ![chinese_garden-6](https://i.imgur.com/MAjTpL0.jpg)     | ![ahornsteig-6](https://i.imgur.com/Yn0RuMR.jpg)      | ![autumn_road-0](https://i.imgur.com/rmbU5mf.jpg)    | ![country_club-2](https://i.imgur.com/7NmoiZi.jpg)      |

### Parameters sampling

Random camera parameters are sampled with the following distributions:

| Parameter                     | Distribution | Values                                                       |
| ----------------------------- | ------------ | ------------------------------------------------------------ |
| Focal lenght (mm)             | Lognormal    | <img src="https://render.githubusercontent.com/render/math?math=\mu=14, \sigma=16">|
| Pitch, midpoint (image units) | Normal       | <img src="https://render.githubusercontent.com/render/math?math=\mu=0.523, \sigma=0.3">|
| Roll (°)                      | Cauchy       | <img src="https://render.githubusercontent.com/render/math?math=x_0=0, \gamma\in \{0.001, 0.1\}">|
| Distortion                    | Triangular   | <img src="https://render.githubusercontent.com/render/math?math=c \in \{0.3, 1\}">
| Aspect ratio                  | Varying      | {1:1(9\%), 5:4(1\%), 4:3(66\%), 3:2 (20\%), 16:9 (4\%)}
| Orientation                   | Varying      | {portrait (20%), landscape (80%)}

## Perceptual measure
In our paper, we conduct a large-scale study where we ask participants to judge the realism of 3D objects composited with correct and biased camera calibration parameters. From the results of this study, we define a perceptual measure that quantifies how sensitive humans are to errors in camera parameters. The perceptual measure goes from 50% (low sensitivity, humans do not notice the error) to 100% (high sensitivity, the error is easily noticeable).

### Usage
```
from perceptual_measure import pitch_perceptual_measure, roll_perceptual_measure, hfov_perceptual_measure, distortion_perceptual_measure
```

For example, on an image with a ground truth roll of 15° and an estimated roll of 10° (error of 15-10=5°), the perceptual measure would be

```
roll_perceptual_measure(value=15, error=5)
> 62.34
```

On the same image, for increasing roll errors, we get:

```
roll_perceptual_measure([15, 15, 15, 15, 15, 15], [0, 5, 10, 15, 20, 25])
> [50.0, 62.34, 74.68, 87.15, 99.19, nan]
```

nan means that the parameter value or error is outside of the ranges used in our study.
