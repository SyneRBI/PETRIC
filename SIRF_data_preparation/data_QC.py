"""Basic QC plots
Reads data in the current directory and makes various plots, saved as .png

Usage:
  data_QC.py [options]

Options:
  -h, --help
  --srcdir=<path>        pathname. Will default to current directory unless dataset is set
  --skip_sino_profiles   do not plot the sinogram profiles
  --transverse_slice=<i>  idx [default: -1]
  --coronal_slice=<c>    idx [default: -1]
  --sagittal_slice=<s>   idx [default: -1]
  --dataset=<name>       dataset name. if set, it is used to override default slices

Note that -1 one means to use middle of image
"""
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.4.0'

import os
import os.path
from ast import literal_eval
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from docopt import docopt
from scipy import ndimage

import sirf.STIR as STIR
from SIRF_data_preparation.data_utilities import the_data_path
from SIRF_data_preparation.dataset_settings import get_settings

STIR.AcquisitionData.set_storage_scheme('memory')


def plot_sinogram_profile(prompts, background, sumaxis=(0, 1), select=0, srcdir='./'):
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
    plt.savefig(os.path.join(srcdir, 'prompts_background_profiles.png'))


def plot_image(image, save_name=None, transverse_slice=-1, coronal_slice=-1, sagittal_slice=-1, vmin=0, vmax=None,
               alpha=None, **kwargs):
    """
    Plot transverse/coronal/sagital slices through sirf.STIR.ImageData
    """
    if transverse_slice < 0:
        transverse_slice = image.dimensions()[0] // 2
    if coronal_slice < 0:
        coronal_slice = image.dimensions()[1] // 2
    if sagittal_slice < 0:
        sagittal_slice = image.dimensions()[2] // 2
    if vmax is None:
        vmax = image.max()

    arr = image.as_array()
    alpha_trans = None
    alpha_cor = None
    alpha_sag = None
    if alpha is not None:
        alpha_arr = alpha.as_array()
        alpha_trans = alpha_arr[transverse_slice, :, :]
        alpha_cor = alpha_arr[:, coronal_slice, :]
        alpha_sag = alpha_arr[:, :, sagittal_slice]

    ax = plt.subplot(131)
    plt.imshow(arr[transverse_slice, :, :], vmin=vmin, vmax=vmax, alpha=alpha_trans, **kwargs)
    ax.set_title(f"T={transverse_slice}")
    ax = plt.subplot(132)
    plt.imshow(arr[:, coronal_slice, :], vmin=vmin, vmax=vmax, alpha=alpha_cor, **kwargs)
    ax.set_title(f"C={coronal_slice}")
    ax = plt.subplot(133)
    plt.imshow(arr[:, :, sagittal_slice], vmin=vmin, vmax=vmax, alpha=alpha_sag, **kwargs)
    ax.set_title(f"S={sagittal_slice}")
    plt.colorbar(shrink=.6)
    if save_name is not None:
        plt.savefig(save_name + '_slices.png')
        plt.suptitle(os.path.basename(save_name))


def plot_image_if_exists(prefix, **kwargs):
    if os.path.isfile(prefix + '.hv'):
        im = STIR.ImageData(prefix + '.hv')
        plt.figure()
        plot_image(im, prefix, **kwargs)
        return im
    else:
        print(f"Image {prefix}.hv does not exist")
        return None


def VOI_mean(image, VOI):
    return float((image * VOI).sum() / VOI.sum())


def VOI_checks(allVOInames, OSEM_image=None, reference_image=None, srcdir='.', **kwargs):
    if len(allVOInames) == 0:
        return
    OSEM_VOI_values = []
    ref_VOI_values = []
    allVOIs = None
    VOIkwargs = kwargs.copy()
    VOIkwargs['vmax'] = 1
    VOIkwargs['vmin'] = 0
    for VOIname in allVOInames:
        prefix = os.path.join(srcdir, VOIname)
        filename = prefix + '.hv'
        if not os.path.isfile(filename):
            print(f"VOI {VOIname} does not exist")
            continue
        VOI = STIR.ImageData(filename)
        VOI_arr = VOI.as_array()
        COM = np.rint(ndimage.center_of_mass(VOI_arr))
        num_voxels = VOI_arr.sum()
        print(f"VOI: {VOIname}: COM (in indices): {COM} voxels {num_voxels} = {num_voxels * np.prod(VOI.spacing)} mm^3")
        plt.figure()
        plot_image(VOI, save_name=prefix, vmin=0, vmax=1, transverse_slice=int(COM[0]), coronal_slice=int(COM[1]),
                   sagittal_slice=int(COM[2]))

        # construct transparency image
        if VOIname == 'VOI_whole_object':
            VOI /= 2
        if allVOIs is None:
            allVOIs = VOI.clone()
        else:
            allVOIs += VOI
        if OSEM_image is not None:
            OSEM_VOI_values.append(VOI_mean(OSEM_image, VOI))
        if reference_image:
            ref_VOI_values.append(VOI_mean(reference_image, VOI))
    allVOIs /= allVOIs.max()

    if OSEM_image is not None:
        plt.figure()
        plot_image(OSEM_image, alpha=allVOIs, save_name="OSEM_image_and_VOIs", **kwargs)

    # unformatted print of VOI values for now
    print(allVOInames)
    print(OSEM_VOI_values)
    print(ref_VOI_values)


def main(argv=None):
    args = docopt(__doc__, argv=argv, version=__version__)
    dataset = args['--dataset']
    srcdir = args['--srcdir']
    skip_sino_profiles = args['--skip_sino_profiles']
    slices = {}
    slices["transverse_slice"] = literal_eval(args['--transverse_slice'])
    slices["coronal_slice"] = literal_eval(args['--coronal_slice'])
    slices["sagittal_slice"] = literal_eval(args['--sagittal_slice'])

    if (dataset):
        if srcdir is None:
            srcdir = the_data_path(dataset)
        settings = get_settings(dataset)
        for key in slices.keys():
            if slices[key] == -1 and key in settings.slices:
                slices[key] = settings.slices[key]
    else:
        if srcdir is None:
            srcdir = os.getcwd()

    if not skip_sino_profiles:
        acquired_data = STIR.AcquisitionData(os.path.join(srcdir, 'prompts.hs'))
        additive_term = STIR.AcquisitionData(os.path.join(srcdir, 'additive_term.hs'))
        mult_factors = STIR.AcquisitionData(os.path.join(srcdir, 'mult_factors.hs'))
        background = additive_term * mult_factors
        plot_sinogram_profile(acquired_data, background, srcdir=srcdir)

    OSEM_image = plot_image_if_exists(os.path.join(srcdir, 'OSEM_image'), **slices)
    plot_image_if_exists(os.path.join(srcdir, 'kappa'), **slices)
    reference_image = plot_image_if_exists(os.path.join(srcdir, 'PETRIC/reference_image'), **slices)

    VOIdir = os.path.join(srcdir, 'PETRIC')
    allVOInames = [os.path.basename(str(voi)[:-3]) for voi in Path(VOIdir).glob("VOI_*.hv")]
    VOI_checks(allVOInames, OSEM_image, reference_image, srcdir=VOIdir, **slices)
    plt.show()


if __name__ == '__main__':
    main()
