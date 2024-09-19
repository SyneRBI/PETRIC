"""Create OSEM and kappa images for PETRIC

Usage:
  create_initial_images.py <data_path> [--help | options]

Arguments:
  <data_path>  path to data files

Options:
  -t <template_image>, --template_image=<template_image>  filename (relative to <data_path>) of image to use
                                                          for data sizes [default: PETRIC/VOI_whole_object.hv]
  -s <xy-size>, --xy-size=<xy-size>  force xy-size (do not use when using VOIs as init) [default: -1]
  -S <subsets>, --subsets=<subsets>  number of subsets [default: 2]
  -i <subiterations>, --subiterations=<subiterations>     number of sub-iterations [default: 14]
"""
# Copyright 2024 Rutherford Appleton Laboratory STFC
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.2.0'

import logging
import math
import os

from docopt import docopt

import sirf.STIR as STIR
from sirf.contrib.partitioner import partitioner

log = logging.getLogger('create_initial_images')
STIR.AcquisitionData.set_storage_scheme('memory')


def create_acq_model_and_obj_fun(acquired_data, additive_term, mult_factors, template_image):
    """Create an acquisition model and objective function, corresponding to the given data"""
    # We could construct this by hand here, but instead will just use `partitioner.data_partition`
    # with 1 subset, which will then do the work for us.
    num_subsets = 1
    _, acq_models, obj_funs = partitioner.data_partition(acquired_data, additive_term, mult_factors, num_subsets,
                                                         initial_image=template_image)
    return (acq_models[0], obj_funs[0])


def scale_initial_image(acquired_data, additive_term, mult_factors, template_image, obj_fun):
    """
    Return a uniform image that has a reasonable "scale" (i.e. image values) for the data given.

    If there is an additive term, OSEM can be a bit slow to converge if the initial image has very wrong
    image values. Here we find a scale such that the sum of the forward projection of the initial image is
    equal to the sum of the acquired data.

    WARNING: assumes that obj_fun has been set_up already
    """
    data_sum = (acquired_data.sum() - (additive_term * mult_factors).sum())
    if data_sum <= 0 or math.isinf(data_sum) or math.isnan(data_sum):
        raise ValueError("Something wrong with input data. Sum of (prompts-background) is negative:"
                         f" sum prompts: {acquired_data.sum()}, sum corrected: {data_sum}")
    ratio = data_sum / (obj_fun.get_subset_sensitivity(0).sum() * obj_fun.get_num_subsets())
    return template_image.allocate(ratio)


def OSEM(obj_fun, initial_image, num_updates=14, num_subsets=2):
    """
    run OSEM

    WARNING: this modifies the `obj_fun` by setting its number of subsets. This is unfortunate of course.
    """
    recon = STIR.OSMAPOSLReconstructor()
    recon.set_objective_function(obj_fun)
    recon.set_current_estimate(initial_image)
    recon.set_num_subsets(num_subsets)
    recon.set_num_subiterations(num_updates)
    recon.set_up(initial_image)
    recon.process()
    return recon.get_output()


def compute_kappa_image(obj_fun, initial_image):
    """
    Computes a "kappa" image for a prior as sqrt(H.1). This will attempt to give uniform "perturbation response".
    See Yu-jung Tsai et al. TMI 2020 https://doi.org/10.1109/TMI.2019.2913889

    WARNING: Assumes the objective function has been set-up already
    """
    minus_Hessian_row_sum = -1 * obj_fun.multiply_with_Hessian(initial_image, initial_image.allocate(1))
    return minus_Hessian_row_sum.maximum(0).power(.5)


def main(argv=None):
    args = docopt(__doc__, argv=argv, version=__version__)
    logging.basicConfig(level=logging.INFO)

    data_path = args['<data_path>']
    log.info("Finding files in %s", data_path)
    xy_size = int(args['--xy-size'])
    subs = int(args['--subsets'])
    siters = int(args['--subiterations'])
    template_image_filename = args['--template_image']
    # engine's messages go to files, except error messages, which go to stdout
    _ = STIR.MessageRedirector('info.txt', 'warnings.txt')

    previous_dir = os.getcwd()
    os.chdir(data_path)
    try:
        acquired_data = STIR.AcquisitionData('prompts.hs')
        additive_term = STIR.AcquisitionData('additive_term.hs')
        mult_factors = STIR.AcquisitionData('mult_factors.hs')
        if template_image_filename == 'None':
            log.info("Constructing template image from prompts")
            template_image = acquired_data.create_uniform_image(0)
        else:
            template_image = STIR.ImageData(template_image_filename)
        if xy_size > 0:
            template_image = template_image.zoom_image(zooms=(1, 1, 1), offsets_in_mm=(0, 0, 0),
                                                       size=(-1, xy_size, xy_size))
        acq_model, obj_fun = create_acq_model_and_obj_fun(acquired_data, additive_term, mult_factors, template_image)

        initial_image = scale_initial_image(acquired_data, additive_term, mult_factors, template_image, obj_fun)
        print(f'Initial_image max: {initial_image.max()}')
        OSEM_image = OSEM(obj_fun, initial_image, num_updates=siters, num_subsets=subs)
        print(f'OSEM_image max: {OSEM_image.max()}')
        OSEM_image.write('OSEM_image.hv')

        kappa = compute_kappa_image(obj_fun, OSEM_image)
        kappa.write('kappa.hv')
    finally:
        os.chdir(previous_dir)
    log.info("done with %s", data_path)


if __name__ == '__main__':
    main()
