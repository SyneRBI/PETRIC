#!/usr/bin/env python
"""Download/Register Hoffman and create VOIs

Usage:
  create_Hoffman_VOIs.py [--help | options]


Options:
  -h, --help
  --dataset=<name>              dataset name (required)
  --srcdir=<path>               pathname. Will default to current directory unless dataset is set
  -s, --skip_write_PETRIC_VOIs  do not write in data/<dataset>/PETRIC
"""

# Copyright 2024 University College London
# Licence: Apache-2.0

# %% imports
import os
import sys
import typing
from pathlib import Path
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import requests
import scipy.ndimage as ndimage
from docopt import docopt

import sirf.STIR as STIR
from SIRF_data_preparation.data_QC import plot_image
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path
from SIRF_data_preparation.registration_utilities import STIR_to_nii, STIR_to_nii_hv, register_it, resample_STIR

# %%
__version__ = "0.1.1"

write_PETRIC_VOIs = True
if "ipykernel" not in sys.argv[0]: # clunky way to be able to set variables from within jupyter/VScode without docopt
    args = docopt(__doc__, argv=None, version=__version__)

    # logging.basicConfig(level=logging.INFO)

    scanID = args["--dataset"]
    srcdir = args['--srcdir']
    if scanID is None:
        print("Need to set the --dataset argument")
        exit(1)
    if args["--skip_write_PETRIC_VOIs"]:
        write_PETRIC_VOIs = False
else:
    # set it by hand, e.g.
    scanID = "NeuroLF_Hoffman_Dataset"
    srcdir = None
    write_PETRIC_VOIs = False

# %% standard PETRIC directories
if srcdir is None:
    srcdir = the_data_path(scanID)
srcdir = Path(srcdir)
downloaddir = Path(the_orgdata_path("downloads"))
intermediate_data_path = the_orgdata_path(scanID, "processing")
os.makedirs(downloaddir, exist_ok=True)
os.makedirs(intermediate_data_path, exist_ok=True)

print("srcdir:", srcdir)
print("downloaddir:", downloaddir)
print("processingdir:", intermediate_data_path)
print("write_VOIs:", write_PETRIC_VOIs)


# %% Function to find the n-th connected component (counting by size)
def connected_component(arr: npt.NDArray[bool], order=0) -> npt.NDArray[bool]:
    """Return connected component of a given order in an array. order=0 returns the largest."""
    labels, num_labels = ndimage.label(arr)
    num_elems = [(labels == i).sum() for i in range(num_labels)]
    idx = np.argsort(num_elems)[-1 - order]
    return labels == idx


# %%%%%%%%%%%%% Read Hoffman data and find VOIs


# %%
def read_and_downsample_Hoffman(downloaddir: Path) -> STIR.ImageData:
    # Download DICOM data
    name = "3D_DRO_Hoffman_v6_20160331_DICOM"
    Hoffman_dicom_dir = downloaddir / name / "3D_DRO_Hoffman_v6_20160331"
    Hoffman_dicom_filename = Hoffman_dicom_dir / "000001"
    if not Hoffman_dicom_filename.is_file():
        fname = name + ".zip"
        full_fname = downloaddir / fname
        url = "https://depts.washington.edu/petctdro/downloads/" + fname
        r = requests.get(url)
        with open(full_fname, "wb") as f:
            f.write(r.content)
        file = ZipFile(full_fname)
        file.extractall(downloaddir)
    # read
    orgHoffman = STIR.ImageData(str(Hoffman_dicom_filename))
    # check that this is a binary mask (0,1)
    # print(np.unique(orgHoffman.as_array()))
    # combine voxels
    # combine 5 slices, as this data "simulates" a 1:5 contrast
    # also combine 2x2 in-plane pixels as voxel-size is quite small for PET
    zooms = (1.0 / 5, 1.0 / 2, 1.0 / 2)
    Hoffman = orgHoffman.zoom_image(
        zooms=zooms,
        offsets_in_mm=(0, 0, 0),
        size=tuple([np.ceil(d * z) for z, d in zip(zooms, orgHoffman.dimensions())]),
        scaling="preserve_values",
    )
    return Hoffman


# %%
def create_Hoffman_VOIs(Hoffman: STIR.ImageData,) -> typing.Tuple[typing.List[STIR.ImageData], typing.List[str]]:
    """Create VOIs using thresholding etc. Requires that 5 slices were combined to get averages"""
    Hoffman_arr = Hoffman.as_array()
    # Find whole object
    # we want to use ndimage.ndimage.binary_fill_holes to find the whole object. However,
    # that function does not fill holes connected to the boundary, so let's
    # fill the "bottom" boundary plane first, fill the holes, and then reset the boundary
    Hoffman_arr[-9:-1, :, :] = 1
    whole_object_arr = ndimage.binary_fill_holes(Hoffman_arr > 0.0)
    whole_object_arr[-9:-1, :, :] = False
    # get rid over 1 layer of outside voxels
    whole_object_arr = ndimage.binary_erosion(whole_object_arr, iterations=1)
    VOI_whole_object = Hoffman.allocate(0)
    VOI_whole_object.fill(whole_object_arr.astype(np.float32))
    Hoffman_arr *= whole_object_arr
    # find GM/WM/ventricle regions by thresholding etc
    inner_arr = ndimage.binary_erosion(whole_object_arr, iterations=4)
    VOI_GM = Hoffman.allocate(0).fill(Hoffman_arr > 0.85)
    VOI_WM = Hoffman.allocate(0).fill(
        np.logical_and(np.logical_and(Hoffman_arr <= 0.85, Hoffman_arr >= 0.15), inner_arr))
    VOI_ventricles_arr = connected_component(np.logical_and(Hoffman_arr <= 0.01, whole_object_arr), order=1)
    VOI_ventricles = Hoffman.allocate(0).fill(VOI_ventricles_arr)
    # Construct "WM background" region by eroding WM
    VOI_background = VOI_whole_object.clone()
    VOI_background.fill(ndimage.binary_erosion(VOI_WM.as_array(), iterations=2))
    # Done
    VOIs = [VOI_whole_object, VOI_background, VOI_GM, VOI_WM, VOI_ventricles]
    VOInames = ["whole_object", "background", "GM", "WM", "ventricles"]
    return (VOIs, VOInames)


# %% Create VOIs
Hoffman_outdir = Path(the_orgdata_path("Hoffman"))
os.makedirs(Hoffman_outdir, exist_ok=True)
Hoffman = read_and_downsample_Hoffman(downloaddir)
plot_image(Hoffman, save_name=str(Hoffman_outdir / "Hoffman"))
VOIs, VOInames = create_Hoffman_VOIs(Hoffman)
for VOI, n in zip(VOIs, VOInames):
    plt.figure()
    plot_image(VOI, save_name=str(Hoffman_outdir / n))

# %% Save
print(f"Writing VOIs to {Hoffman_outdir}")
VOIs_nii = [STIR_to_nii_hv(VOI, str(Hoffman_outdir / n)) for VOI, n in zip(VOIs, VOInames)]

# %% Give names that make sense (TODO: use dataclass as opposed to list)
VOI_GM = VOIs[2]
VOI_WM = VOIs[3]
# %% show plots if run as script
print("You might have to close all windows to continue")
plt.show()

# %%%%%%%%%%%%% Register VOIs to OSEM_image

# %% Now register this to the reconstructed image
OSEM_image = STIR.ImageData(str(srcdir / "OSEM_image.hv"))
OSEM_image_nii = STIR_to_nii(OSEM_image, os.path.join(intermediate_data_path, "OSEM_image.nii"))

# %% Construct ground-truth image and register
# The PET image is obtained by filling the phantom which has plastic slices giving "apparent" contrast.
# Should be 4:1, but from this phantom, it seems 5:1 (doesn't matter for the registration)
orgGT = VOI_GM*5 + VOI_WM*1
orgGT_nii = STIR_to_nii_hv(orgGT, os.path.join(intermediate_data_path, "orgGT"))

regGT_nii, resampler, _ = register_it(OSEM_image_nii, orgGT_nii)
regGT = resample_STIR(resampler, orgGT_nii, os.path.join(intermediate_data_path, "regGT"))

# %% check registration
plt.figure()
plot_image(regGT)
plt.figure()
plot_image(OSEM_image)
# %% get registered VOIs
datadir = Path(intermediate_data_path)
print(f"Creating and writing registered VOIs to {datadir}")
regVOIs = [resample_STIR(resampler, VOI, str(datadir / ("reg"+n))) for VOI, n in zip(VOIs_nii, VOInames)]
# display registered VOIs
for VOI, n in zip(regVOIs, VOInames):
    plt.figure()
    plot_image(VOI, save_name=str(datadir / n))

# %% write PETRIC VOIs
if write_PETRIC_VOIs:
    datadir = Path(srcdir) / "PETRIC"
    print(f"Writing registered VOIs to {datadir}")
    os.makedirs(datadir, exist_ok=True)
    for VOI, n in zip(regVOIs, VOInames):
        VOI.write(str(datadir / ("VOI_"+n)))
# %%
plt.show()
