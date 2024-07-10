"""Basic QC plots
Reads data in the current directory and makes various plots, saved as .png

Usage:
  data_QC.py [options]

Options:
  -h, --help
"""
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.2.0'

import os

import matplotlib.pyplot as plt
import numpy as np
from docopt import docopt
from pathlib import Path
import os.path
import sirf.STIR as STIR

STIR.AcquisitionData.set_storage_scheme('memory')

def plot_sinogram_profile(prompts, background, sumaxis=(0, 1), select=0):
    """
    Plot a profile through sirf.STIR.AcquisitionData

    sumaxis: axes to sum over (passed to numpy.sum(..., axis))
    select: element to select after summing
    """
    # we will average over all sinograms to reduce noise
    plt.figure()
    ax = plt.subplot(111)
    plt.plot(np.sum(prompts.as_array(), axis=sumaxis)[select, :], label='prompts')
    plt.plot(np.sum(background.as_array(), axis=sumaxis)[select, :], label='background')
    ax.legend()
    plt.savefig('prompts_background_profiles.png')


def plot_image(image, save_name=None,
               transverse_slice=-1,
               coronal_slice=-1,
               sagital_slice=-1,
               vmin=0, vmax=None):
    """
    Plot a profile through sirf.STIR.ImageData
    """
    if transverse_slice < 0:
        transverse_slice = image.dimensions()[0] // 2
    if coronal_slice < 0:
        coronal_slice = image.dimensions()[1] // 2
    if sagital_slice < 0:
        sagital_slice = image.dimensions()[2] // 2
    if vmax is None:
        vmax = image.max()

    arr = image.as_array()
    plt.figure()
    plt.subplot(131)
    plt.imshow(arr[transverse_slice, :, :], vmin=vmin, vmax=vmax)
    plt.subplot(132)
    plt.imshow(arr[:, coronal_slice, :], vmin=vmin, vmax=vmax)
    plt.subplot(133)
    plt.imshow(arr[:,:, sagital_slice], vmin=vmin, vmax=vmax)
    plt.colorbar(shrink=.6)
    if save_name is not None:
        plt.savefig(save_name + '_slices.png')
        plt.suptitle(os.path.basename(save_name))


def plot_image_if_exists(prefix, **kwargs):
    if os.path.isfile(prefix + '.hv'):
        im = STIR.ImageData(prefix + '.hv')
        plot_image(im, prefix, *kwargs)
        return im
    else:
        return None

def VOI_mean(image, VOI):
    return float((image*VOI).sum() / VOI.sum())

def VOI_checks(allVOInames, OSEM_image, reference_image, srcdir='.'):
    if len(allVOInames) == 0:
        return
    OSEM_VOI_values = []
    ref_VOI_values = []
    for VOIname in allVOInames:
        VOI = plot_image_if_exists(os.path.join(srcdir, VOIname))
        if OSEM_image:
            OSEM_VOI_values.append(VOI_mean(OSEM_image, VOI))
        if reference_image:
            ref_VOI_values.append(VOI_mean(reference_image, VOI))
    # unformatted print of VOI values for now
    print(allVOInames)
    print(OSEM_VOI_values)
    print(ref_VOI_values)


def main(argv=None):
    args = docopt(__doc__, argv=argv, version=__version__)

    srcdir = './'
    acquired_data = STIR.AcquisitionData(srcdir+'prompts.hs')
    additive_term = STIR.AcquisitionData('additive_term.hs')
    mult_factors = STIR.AcquisitionData('mult_factors.hs')
    background = additive_term * mult_factors
    plot_sinogram_profile(acquired_data, background)

    OSEM_image = plot_image_if_exists('OSEM_image')
    plot_image_if_exists('kappa')
    reference_image = plot_image_if_exists('reference_image')

    VOIdir = os.path.join(srcdir, "PETRIC")
    allVOInames = [ os.path.basename(str(voi)[:-3]) for voi in Path(VOIdir).glob("VOI_*.hv")]
    VOI_checks(allVOInames, OSEM_image, reference_image, srcdir=VOIdir)
    plt.show()

if __name__ == '__main__':
    main()
