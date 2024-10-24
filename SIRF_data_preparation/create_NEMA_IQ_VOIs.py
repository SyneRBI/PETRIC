#!/usr/bin/env python
"""Create VOIs for a scan of the NEMA IQ phantom

Usage:
  create_NEMA_IQ_VOIs.py [--help | options]


Options:
  -h, --help
  --dataset=<name>              dataset name (required)
  --srcdir=<path>               pathname. Will default to current directory unless dataset is set
  --central_VOI=<bool>          Use the normal background VOI (in the centre of the phantom) or a
                                VOI "below" the largest sphere [default: True]
  --angle_smallest_sphere=<a>   angle (in degrees) of smallest sphere [default: 210]
  --spheres=<s>                 string to be parsed as tuple of sphere numbers (1 is smallest) [default: (1,3,5)]
"""

# Copyright 2024 University College London
# Licence: Apache-2.0

# %%
# %load_ext autoreload
# %autoreload 2
# %% imports
import ast
import os
import sys
import typing
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import scipy.ndimage as ndimage
from docopt import docopt

import sirf.contrib.NEMA.generate_nema_rois as generate_nema_rois
import sirf.STIR as STIR
from SIRF_data_preparation.data_QC import VOI_checks, plot_image
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path
from SIRF_data_preparation.dataset_settings import get_settings

# %%
__version__ = "0.1.0"

if "ipykernel" not in sys.argv[0]: # clunky way to be able to set variables from within jupyter/VScode without docopt
    args = docopt(__doc__, argv=None, version=__version__)

    # logging.basicConfig(level=logging.INFO)
    scanID = args["--dataset"]
    srcdir = args['--srcdir']
    if scanID is None:
        print("Need to set the --dataset argument")
        exit(1)
    angle_smallest_sphere = float(args["--angle_smallest_sphere"])
    central_VOI = ast.literal_eval(args["--central_VOI"])
    spheres = ast.literal_eval(args["--spheres"])
else:
    # set it by hand, e.g.
    scanID = "GE_D690_NEMA_IQ"
    srcdir = None
    central_VOI = False
    spheres = (2, 3, 5)
    angle_smallest_sphere = 30

# %% standard PETRIC directories
if srcdir is None:
    srcdir = the_data_path(scanID)
srcdir = Path(srcdir)
intermediate_data_path = Path(the_orgdata_path(scanID, "processing"))
os.makedirs(intermediate_data_path, exist_ok=True)
settings = get_settings(scanID)
slices = settings.slices

print("srcdir:", srcdir)
print("processingdir:", intermediate_data_path)
print("angle_smallest_sphere:", angle_smallest_sphere)
print("central_VOI:", central_VOI)
print("spheres:", spheres)


# %% Function to find the n-th connected component (counting by size)
def connected_component(arr: npt.NDArray[bool], order=0) -> npt.NDArray[bool]:
    """Return connected component of a given order in an array. order=0 returns the largest."""
    labels, num_labels = ndimage.label(arr)
    num_elems = [(labels == i).sum() for i in range(num_labels)]
    idx = np.argsort(num_elems)[-1 - order]
    return labels == idx


def read_unregistered_VOIs(intermediate_datadir: Path) -> typing.List[STIR.ImageData]:
    orgVOIs = []
    for i in range(1, 8):
        orgVOIs.append(STIR.ImageData(str(intermediate_datadir / f"unregistered_sphere{i}.nii")))
    return orgVOIs


def read_orgVOIs(intermediate_datadir: Path) -> typing.List[STIR.ImageData]:
    orgVOIs = []
    for i in range(1, 8):
        orgVOIs.append(STIR.ImageData(str(intermediate_datadir / f"S{i}.nii")))
    return orgVOIs


def create_whole_object_mask(reference_image: STIR.ImageData) -> STIR.ImageData:
    whole_object_mask = reference_image.clone()
    ref_arr = reference_image.as_array()
    whole_object_mask.fill(ndimage.binary_erosion(ref_arr > np.percentile(ref_arr, 99) / 20, iterations=2))
    # plot_image(whole_object_mask, **slices)
    return whole_object_mask


def create_background_VOI(orgVOIs: typing.List[STIR.ImageData], central_VOI: bool) -> STIR.ImageData:
    if central_VOI:
        return orgVOIs[6]
    # This is the NEMA with "lung" so need to move background somewhere else
    # will use the largest sphere VOI and shift it down
    background_mask = orgVOIs[5].clone()
    background_arr = background_mask.as_array()
    # COM = ndimage.center_of_mass(background_arr)
    z_voxel_size = background_mask.voxel_sizes()[0]
    # 37 mm diameter
    z_shift = int(np.floor(37 * 1.2 / z_voxel_size))
    background_arr = np.concatenate((
        background_arr[0:z_shift, :, :] * 0,
        background_arr[0:-z_shift, :, :],
    ))
    background_mask.fill(background_arr)
    return background_mask


# %%
reference_image = STIR.ImageData(str(srcdir / 'OSEM_image.hv'))
plot_image(reference_image, **slices)
# %%
thresholded_image = reference_image.clone()
thresholded_arr = thresholded_image.as_array()
thresholded_arr[thresholded_arr < np.max(thresholded_arr) / 5] = 0
thresholded_image.fill(thresholded_arr)
# %%
# currently needs trailing slash
generate_nema_rois.data_output_path = str(intermediate_data_path) + "/"
generate_nema_rois.generate_nema_rois(thresholded_image, angle_smallest=angle_smallest_sphere)
# %%
unregVOIs = read_unregistered_VOIs(intermediate_data_path)
orgVOIs = read_orgVOIs(intermediate_data_path)
# %%
whole_object_mask = create_whole_object_mask(reference_image)
background_mask = create_background_VOI(orgVOIs, central_VOI)
sphere_VOIs = [orgVOIs[i - 1] for i in spheres]
# %%
VOIs = [whole_object_mask, background_mask] + sphere_VOIs
VOInames = ["VOI_whole_object", "VOI_background"] + [f"VOI_sphere{s}" for s in spheres]

# %% write PETRIC VOIs
datadir = Path(srcdir) / "PETRIC"
print(f"Writing VOIs to {datadir}")
os.makedirs(datadir, exist_ok=True)
for VOI, n in zip(VOIs, VOInames):
    VOI.write(str(datadir / n))
# %%
VOI_checks(VOInames, OSEM_image=reference_image, reference_image=None, srcdir=datadir)
# %%
plt.show()
