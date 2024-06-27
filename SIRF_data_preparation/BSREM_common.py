"""Functions to run BSREM with some monitoring via TensorBoard."""
# Authors: Kris Thielemans, Casper da Costa Luis
# Licence: Apache-2.0
# Copyright (C) 2024 University College London
# Copyright (C) 2024 STFC, UK Research and Innovation

import csv
from pathlib import Path

from numpy import clip, loadtxt
from tensorboardX import SummaryWriter

import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks
from sirf.contrib.BSREM.BSREM import BSREM1  # , BSREM2
from sirf.contrib.partitioner import partitioner


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


class Iterations(callbacks.Callback):
    """Saves algo.x as `iter_{algo.iteration:04d}.hv` and algo.loss in `objectives.csv`"""
    def __init__(self, verbose=1, savedir='.', csv_file='objectives.csv'):
        super().__init__(verbose)
        self.savedir = Path(savedir)
        self.savedir.mkdir(parents=True, exist_ok=True)
        self.csv = csv.writer((self.savedir / csv_file).open("w", newline=""))
        self.csv.writerow(("iter", "objective"))

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval == 0 or algo.iteration == algo.max_iteration:
            algo.x.write(str(self.savedir / f'iter_{algo.iteration:04d}.hv'))
            self.csv.writerow((algo.iterations, algo.loss))
        if algo.iteration == algo.max_iteration:
            algo.x.write(str(self.savedir / f'iter_final.hv'))


class TBoard(callbacks.Callback):
    def __init__(self, verbose=1, transverse_slice=None, coronal_slice=None, vmax=None, logdir=None):
        super().__init__(verbose)
        self.transverse_slice = transverse_slice
        self.coronal_slice = coronal_slice
        self.vmax = vmax
        self.x_prev = None
        self.tb = SummaryWriter(logdir=logdir)

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval != 0 and algo.iteration != algo.max_iteration:
            return
        # initialise `None` values
        self.transverse_slice = algo.x.dimensions()[0] // 2 if self.transverse_slice is None else self.transverse_slice
        self.coronal_slice = algo.x.dimensions()[1] // 2 if self.coronal_slice is None else self.coronal_slice
        self.vmax = algo.x.max() if self.vmax is None else self.vmax

        self.tb.add_scalar("objective", algo.get_last_loss(), algo.iteration)
        if self.x_prev is not None:
            normalised_change = (algo.x - self.x_prev).norm() / algo.x.norm()
            self.tb.add_scalar("normalised_change", normalised_change, algo.iteration)
        self.x_prev = algo.x.clone()
        self.tb.add_image("transverse",
                          clip(algo.x.as_array()[self.transverse_slice:self.transverse_slice + 1] / self.vmax, 0, 1),
                          algo.iteration)
        self.tb.add_image("coronal", clip(algo.x.as_array()[None, :, self.coronal_slice] / self.vmax, 0, 1),
                          algo.iteration)


def run(num_subsets: int = 7, num_updates: int = 5000, save_interval: int = 10, transverse_slice: int | None = None,
        coronal_slice: int | None = None):
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

    # read data
    acquired_data = STIR.AcquisitionData('prompts.hs')
    additive_term = STIR.AcquisitionData('additive_term.hs')
    mult_factors = STIR.AcquisitionData('mult_factors.hs')

    # read initial image
    OSEM_image = STIR.ImageData('OSEM_image.hv')

    # read/construct RDP
    kappa = STIR.ImageData('kappa.hv')
    if Path('penalisation_factor.txt').is_file():
        penalty_strength = float(loadtxt('penalisation_factor.txt'))
    else:
        penalty_strength = 1 / 700  # default choice
    prior = construct_RDP(penalty_strength, OSEM_image, kappa)

    data, acq_models, obj_funs = partitioner.data_partition(acquired_data, additive_term, mult_factors, num_subsets,
                                                            initial_image=OSEM_image)
    add_prior_to_obj_funs(obj_funs, prior, OSEM_image)
    bsrem1 = BSREM1(data, obj_funs, initial=OSEM_image, initial_step_size=.3, relaxation_eta=.01,
                    update_objective_interval=save_interval)
    # WARNING: should specify logdir here to avoid writing to data source dir
    tb_cbk = TBoard(transverse_slice=transverse_slice, coronal_slice=coronal_slice, logdir=None)
    bsrem1.run(iterations=num_updates,
               callbacks=[callbacks.ProgressCallback(), Iterations(savedir=tb_cbk.tb.logdir), tb_cbk])
