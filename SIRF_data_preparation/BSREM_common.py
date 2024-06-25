from numpy import clip
from tensorboardX import SummaryWriter

import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks
from sirf.contrib.BSREM.BSREM import BSREM1 # , BSREM2
# Import functionality from the Python files in SIRF-Contribs. (Note that in most set-ups, this will be from the installed files.)
from sirf.contrib.partitioner import partitioner
#from sirf.Utilities import examples_data_path
#from sirf_exercises import exercises_data_path


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


class TensorBoardCallback(callbacks.Callback):
    def __init__(self, verbose=1, im_slice=None, logdir=None):
        super().__init__(verbose)
        self.im = {}
        self.slice = im_slice
        self.dims = None
        self.matplotlib = False
        self.tb = SummaryWriter(logdir=logdir)

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval == 0:
            self.tb.add_scalar("objective", algo.get_last_loss(), algo.iteration)
            if self.verbose >= 1:
                algo.x.write(f'{self.tb.logdir}/iter_{algo.iteration:04d}.hv')
            self.im[algo.iteration] = algo.x.clone()
            self.dims = self.dims or algo.x.dimensions()
            self.cmax = self.cmax or algo.x.max()
            im_slice = self.dims[0] // 2 if self.slice is None else self.slice
            cor_slice = self.dims[1] // 2
            self.tb.add_image("transverse", clip(algo.x.as_array()[im_slice:im_slice + 1] / self.cmax, 0, 1), algo.iteration)
            self.tb.add_image("coronal", clip(algo.x.as_array()[None, :, cor_slice] / self.cmax, 0, 1), algo.iteration)


def run(num_subsets: int = 7, im_slice: int | None = None):
    """
    num_subsets: number of subsets to use
    im_slice: slice to show in the middle of the image (default: len(image) // 2)
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
    bsrem1 = BSREM1(data, obj_funs, initial=OSEM_image, initial_step_size=.3, relaxation_eta=.05,
                    update_objective_interval=10)
    bsrem1.run(iterations=660, callbacks=[
        callbacks.ProgressCallback(),
        TensorBoardCallback(im_slice=im_slice) # WARNING: should specify logdir here to avoid writing to data source dir
    ])
