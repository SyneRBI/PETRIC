"""Functions to run BSREM with some monitoring via TensorBoard."""
# Authors: Kris Thielemans, Casper da Costa Luis
# Licence: Apache-2.0
# Copyright (C) 2024 University College London
# Copyright (C) 2024 STFC, UK Research and Innovation

from numpy import clip
from tensorboardX import SummaryWriter

import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks
# Import functionality from the Python files in SIRF-Contribs
from sirf.contrib.partitioner import partitioner
from sirf.contrib.BSREM.BSREM import BSREM1 # , BSREM2


# do not modify this one!
def construct_RDP(penalty_strength, initial_image, kappa, max_scaling=1e-3):
    """
    Construct a smoothed Relative Difference Prior (RDP)

    initial_image: used to determine a smoothing factor (epsilon).
    kappa: used to pass voxel-dependent weights.
    """
    prior = STIR.RelativeDifferencePrior()
    # need to make it differentiable
    epsilon = initial_image.max() * max_scaling
    prior.set_epsilon(epsilon)
    prior.set_penalisation_factor(penalty_strength)
    prior.set_kappa(kappa)
    prior.set_up(initial_image)
    return prior


def add_prior_to_obj_funs(obj_funs, prior, initial_image):
    """
    Add prior evenly to every objective function in the obj_funs list.

    WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
    WARNING: modifies elements of obj_funs
    """
    # evenly distribute prior over subsets
    prior.set_penalisation_factor(prior.get_penalisation_factor() / len(obj_funs))
    prior.set_up(initial_image)
    for f in obj_funs:
        f.set_prior(prior)


class SaveCallback(callbacks.Callback):

    def __init__(self, verbose=1, savedir='.'):
        super().__init__(verbose)
        self.savedir = savedir

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval == 0:
            algo.x.write(f'{self.savedir}/BSREM_{algo.iteration:04d}.hv')
        if algo.iteration == algo.max_iteration:
            algo.x.write(f'{self.savedir}/BSREM_final.hv')

        import csv
        with open('BSREM_obj_fun.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            # Write each row of the list to the CSV
            writer.writerows(zip(algo.iterations, algo.loss))

class TensorBoardCallback(callbacks.Callback):

    def __init__(self, verbose=1, transverse_slice=None, coronal_slice=None, vmax=None, logdir=None):
        super().__init__(verbose)
        self.transverse_slice = transverse_slice
        self.coronal_slice = coronal_slice
        self.dims = None
        self.vmax = vmax
        self.prev = None
        self.matplotlib = False
        self.tb = SummaryWriter(logdir=logdir)

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval == 0 or algo.iteration == algo.max_iteration:
            self.tb.add_scalar("objective", algo.get_last_loss(), algo.iteration)
            if self.prev:
                normalised_change = (algo.x - self.prev).norm() / algo.x.norm()
                self.tb.add_scalar("normalised_change", normalised_change, algo.iteration)
                
            self.dims = self.dims or algo.x.dimensions()
            self.vmax = self.vmax or algo.x.max()
            transverse_slice = self.dims[0] // 2 if self.transverse_slice is None else self.transverse_slice
            cor_slice = self.dims[1] // 2 if self.coronal_slice is None else self.coronal_slice
            
            self.tb.add_image("transverse", clip(algo.x.as_array()[transverse_slice:transverse_slice + 1] / self.vmax, 0, 1), algo.iteration)
            self.tb.add_image("coronal", clip(algo.x.as_array()[None, :, cor_slice] / self.vmax, 0, 1), algo.iteration)

            self.prev = algo.x.clone()


def run(num_subsets: int = 7, num_updates: int = 5000, save_interval:int = 10, transverse_slice: int | None = None, coronal_slice: int | None = None):
    """
    num_subsets: number of subsets to use
    num_updates: number of updates ("iterations" in CIL terminology) to use
    transverse_slice: slice to show for transverse image (default: len(image) // 2)
    coronal_slice: slice to show for the coronal image (default: len(image[0]) // 2)
    """
    # Needed for get_subsets()
    STIR.AcquisitionData.set_storage_scheme('memory')
    # set-up redirection of STIR messages to files
    _ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
    # fewer messages from STIR and SIRF (set to higher value to diagnose have problems)
    STIR.set_verbosity(0)

    # read
    acquired_data = STIR.AcquisitionData('prompts.hs')
    additive_term = STIR.AcquisitionData('additive_term.hs')
    mult_factors = STIR.AcquisitionData('mult_factors.hs')
    OSEM_image = STIR.ImageData('OSEM_image.hv')
    kappa = STIR.ImageData('kappa.hv')
    penalty_strength = 1 / 700

    prior = construct_RDP(penalty_strength, OSEM_image, kappa)

    data, acq_models, obj_funs = partitioner.data_partition(acquired_data, additive_term,
                                                            mult_factors, num_subsets,
                                                            initial_image=OSEM_image)
    add_prior_to_obj_funs(obj_funs, prior, OSEM_image)
    bsrem1 = BSREM1(data, obj_funs, initial=OSEM_image, initial_step_size=.3, relaxation_eta=.01,
                    update_objective_interval=save_interval)
    bsrem1.run(iterations=num_updates, callbacks=[
        callbacks.ProgressCallback(),
        SaveCallback(),
        TensorBoardCallback(transverse_slice=transverse_slice, coronal_slice=coronal_slice) # WARNING: should specify logdir here to avoid writing to data source dir
    ])
