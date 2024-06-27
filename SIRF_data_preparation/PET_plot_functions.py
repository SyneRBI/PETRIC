'''Some functions for plotting used in the examples'''
# Licence: Apache-2.0
# Copyright 2020-2021 University College London
import matplotlib.pyplot as plt
import numpy as np

import sirf.STIR as PET


def plot_sinogram_profile(prompts, randoms=None, scatter=None, sumaxis=(0, 1), select=0):
    """
    Plot a profile through sirf.STIR.AcquisitionData

    sumaxis: axes to sum over (passed to numpy.sum(..., axis))
    select: element to select after summing
    """
    if isinstance(prompts, str):
        prompts = PET.AcquisitionData(prompts)
    if isinstance(randoms, str):
        randoms = PET.AcquisitionData(randoms)
    if isinstance(scatter, str):
        scatter = PET.AcquisitionData(scatter)
    # we will average over all sinograms to reduce noise
    plt.figure()
    ax = plt.subplot(111)
    plt.plot(np.sum(prompts.as_array(), axis=sumaxis)[select, :], label='prompts')
    if randoms is None:
        if scatter is not None:
            plt.plot(np.sum(scatter.as_array(), axis=sumaxis)[select, :], label='scatter')
    else:
        randoms_as_array = randoms.as_array()
        plt.plot(np.sum(randoms_as_array, axis=sumaxis)[select, :], label='randoms')
        if scatter is not None:
            plt.plot(np.sum(scatter.as_array() + randoms_as_array, axis=sumaxis)[select, :], label='randoms+scatter')
    ax.legend()
    plt.show()
