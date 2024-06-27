import csv
import os
from collections import namedtuple
from pathlib import Path
from time import time

from numpy import clip, inf, loadtxt
from tensorboardX import SummaryWriter

import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks as cbks
from sirf.contrib.partitioner import partitioner

TEAM = os.getenv("GITHUB_REPOSITORY", "SyneRBI/PETRIC-").split("/PETRIC-", 1)[-1]
VERSION = os.getenv("GITHUB_REF_NAME", "")
OUTDIR = Path(f"/o/logs/{TEAM}/{VERSION}" if TEAM and VERSION else "./output")
SRCDIR = Path("/mnt/share/petric")


class SaveIters(cbks.Callback):
    """Saves `algo.x` as "iter_{algo.iteration:04d}.hv" and `algo.loss` in `csv_file`"""
    def __init__(self, verbose=1, outdir=OUTDIR, csv_file='objectives.csv'):
        super().__init__(verbose)
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.csv = csv.writer((self.outdir / csv_file).open("w", newline=""))
        self.csv.writerow(("iter", "objective"))

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval == 0 or algo.iteration == algo.max_iteration:
            algo.x.write(str(self.outdir / f'iter_{algo.iteration:04d}.hv'))
            self.csv.writerow((algo.iterations, algo.loss))
        if algo.iteration == algo.max_iteration:
            algo.x.write(str(self.outdir / 'iter_final.hv'))


class TensorBoard(cbks.Callback):
    def __init__(self, verbose=1, transverse_slice=None, coronal_slice=None, vmax=None, logdir=OUTDIR):
        super().__init__(verbose)
        self.transverse_slice = transverse_slice
        self.coronal_slice = coronal_slice
        self.vmax = vmax
        self.x_prev = None
        self.tb = SummaryWriter(logdir=str(logdir))

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


class MetricsWithTimeout(cbks.Callback):
    """Stops the algorithm after `seconds`"""
    def __init__(self, seconds=300, outdir=OUTDIR, transverse_slice=None, coronal_slice=None, verbose=1):
        super().__init__(verbose)
        self.callbacks = [
            cbks.ProgressCallback(),
            SaveIters(outdir=outdir),
            TensorBoard(logdir=outdir, transverse_slice=transverse_slice, coronal_slice=coronal_slice)]
        self.limit = time() + seconds

    def __call__(self, algorithm: Algorithm):
        if (now := time()) > self.limit:
            raise StopIteration
        if self.callbacks:
            for c in self.callbacks:
                c(algorithm)
            self.limit += time() - now


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


Dataset = namedtuple('Dataset', [
    'data', 'acq_models', 'obj_funs', 'prior', 'penalty_strength', 'OSEM_image', 'kappa', 'mult_factors',
    'additive_term', 'acquired_data'])


def get_data(num_subsets: int = 7, srcdir=".", outdir=OUTDIR, sirf_verbosity=0):
    srcdir = Path(srcdir)
    outdir = Path(outdir)
    STIR.set_verbosity(sirf_verbosity)                # set to higher value to diagnose problems
    STIR.AcquisitionData.set_storage_scheme('memory') # needed for get_subsets()

    _ = STIR.MessageRedirector(str(outdir / 'BSREM_info.txt'), str(outdir / 'BSREM_warnings.txt'),
                               str(outdir / 'BSREM_errors.txt'))
    acquired_data = STIR.AcquisitionData(str(srcdir / 'prompts.hs'))
    additive_term = STIR.AcquisitionData(str(srcdir / 'additive_term.hs'))
    mult_factors = STIR.AcquisitionData(str(srcdir / 'mult_factors.hs'))
    OSEM_image = STIR.ImageData(str(srcdir / 'OSEM_image.hv'))
    kappa = STIR.ImageData(str(srcdir / 'kappa.hv'))
    if (penalty_strength_file := (srcdir / 'penalisation_factor.txt')).is_file():
        penalty_strength = float(loadtxt(penalty_strength_file))
    else:
        penalty_strength = 1 / 700 # default choice
    prior = construct_RDP(penalty_strength, OSEM_image, kappa)

    data, acq_models, obj_funs = partitioner.data_partition(acquired_data, additive_term, mult_factors, num_subsets,
                                                            initial_image=OSEM_image)
    add_prior_to_obj_funs(obj_funs, prior, OSEM_image)

    return Dataset(data=data, acq_models=acq_models, obj_funs=obj_funs, prior=prior, penalty_strength=penalty_strength,
                   OSEM_image=OSEM_image, kappa=kappa, mult_factors=mult_factors, additive_term=additive_term,
                   acquired_data=acquired_data)


if SRCDIR.is_dir():
    metrics_data_pairs = [
        ([MetricsWithTimeout(outdir=OUTDIR / "mMR_NEMA", transverse_slice=72, coronal_slice=109)],
         get_data(srcdir=SRCDIR / "Siemens_mMR_NEMA_IQ", outdir=OUTDIR / "mMR_NEMA", num_subsets=7)),
        ([MetricsWithTimeout(outdir=OUTDIR / "NeuroLF_Hoffman", transverse_slice=72)],
         get_data(srcdir=SRCDIR / "NeuroLF_Hoffman_Dataset", outdir=OUTDIR / "NeuroLF_Hoffman", num_subsets=16)),
        ([MetricsWithTimeout(outdir=OUTDIR / "Vision600_thorax")],
         get_data(srcdir=SRCDIR / "Siemens_Vision600_thorax", outdir=OUTDIR / "Vision600_thorax", num_subsets=5))]
else:
    metrics_data_pairs = [(None, None)]
# first dataset
metrics, data = metrics_data_pairs[0]

if __name__ == "__main__":
    from main import Submission, submission_callbacks
    assert issubclass(Submission, Algorithm)
    for metrics, data in metrics_data_pairs:
        algo = Submission(data)
        algo.run(inf, callbacks=metrics + submission_callbacks)
