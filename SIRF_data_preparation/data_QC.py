"""Basic QC plots
Reads data in the current directory and makes various plots, saved as .png

Usage:
  data_QC.py [--help ]

Options:
  -h, --help
"""
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.1.0'

import os
import sirf.STIR as STIR
from docopt import docopt
import numpy as np
import matplotlib.pyplot as plt

def plot_sinogram_profile(prompts, background, sumaxis=(0,1), select=0):
    """
    Plot a profile through sirf.STIR.AcquisitionData

    sumaxis: axes to sum over (passed to numpy.sum(..., axis))
    select: element to select after summing
    """
    # we will average over all sinograms to reduce noise
    plt.figure()
    ax = plt.subplot(111)
    plt.plot(np.sum(prompts.as_array(), axis=sumaxis)[select,:], label='prompts')
    plt.plot(np.sum(background.as_array(), axis=sumaxis)[select,:], label='background')
    ax.legend()
    plt.savefig('prompts_background_profiles.png')

def plot_image(image, save_name, transverse_slice=-1, coronal_slice=-1):
    """
    Plot a profile through sirf.STIR.ImageData
    """
    plt.figure()
    if transverse_slice < 0:
        transverse_slice = image.dimensions()[0]//2
    if coronal_slice < 0:
        coronal_slice = image.dimensions()[1]//2
    cmax = image.max()
    arr = image.as_array()
    plt.figure()
    plt.subplot(121)
    plt.imshow(arr[transverse_slice,:,:], vmax=cmax)
    plt.subplot(122)
    plt.imshow(arr[:,coronal_slice,:], vmax=cmax)
    plt.colorbar()
    plt.savefig(save_name + '_slices.png')

def plot_image_if_exists(prefix):
    if os.path.isfile(prefix + '.hv'):
        im = STIR.ImageData(prefix + '.hv')
        plot_image(im, prefix)

STIR.AcquisitionData.set_storage_scheme('memory')

def main(argv=None):
    args = docopt(__doc__, argv=argv, version=__version__)

    acquired_data = STIR.AcquisitionData('prompts.hs')
    additive_term = STIR.AcquisitionData('additive_term.hs')
    mult_factors = STIR.AcquisitionData('mult_factors.hs')
    background = additive_term * mult_factors
    plot_sinogram_profile(acquired_data, background)

    plot_image_if_exists('OSEM_image')
    plot_image_if_exists('kappa')
    plt.show()

if __name__ == '__main__':
    main()