#!/usr/bin/env python
"""
ANY CHANGES TO THIS FILE ARE IGNORED BY THE ORGANISERS.
Only the `main.py` file may be modified by participants.

This file is not intended for participants to use.
It is used by the organisers to run the submissions in a controlled way.
It is included here purely in the interest of transparency.

Usage:
  petric.py [options]

Options:
  --log LEVEL  : Set logging level (DEBUG, [default: INFO], WARNING, ERROR, CRITICAL)
"""
import csv
import logging
import os
from collections import namedtuple
from pathlib import Path
from time import time

import numpy as np
from skimage.metrics import mean_squared_error, peak_signal_noise_ratio
from tensorboardX import SummaryWriter

import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks as cbks
from img_quality_cil_stir import ImageQualityCallback

log = logging.getLogger('petric')
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
            log.debug("saving iter %d...", algo.iteration)
            algo.x.write(str(self.outdir / f'iter_{algo.iteration:04d}.hv'))
            self.csv.writerow((algo.iterations, algo.loss))
            log.debug("...saved")
        if algo.iteration == algo.max_iteration:
            algo.x.write(str(self.outdir / 'iter_final.hv'))


class TensorBoard(cbks.Callback):
    """Log image slices & objective value"""
    def __init__(self, verbose=1, transverse_slice=None, coronal_slice=None, vmax=None, logdir=OUTDIR):
        super().__init__(verbose)
        self.transverse_slice = transverse_slice
        self.coronal_slice = coronal_slice
        self.vmax = vmax
        self.x_prev = None
        self.tb = logdir if isinstance(logdir, SummaryWriter) else SummaryWriter(logdir=str(logdir))

    def __call__(self, algo: Algorithm):
        if algo.iteration % algo.update_objective_interval != 0 and algo.iteration != algo.max_iteration:
            return
        log.debug("logging iter %d...", algo.iteration)
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
                          np.clip(algo.x.as_array()[self.transverse_slice:self.transverse_slice + 1] / self.vmax, 0, 1),
                          algo.iteration)
        self.tb.add_image("coronal", np.clip(algo.x.as_array()[None, :, self.coronal_slice] / self.vmax, 0, 1),
                          algo.iteration)
        log.debug("...logged")


class MetricsWithTimeout(cbks.Callback):
    """Stops the algorithm after `seconds`"""
    def __init__(self, seconds=300, outdir=OUTDIR, transverse_slice=None, coronal_slice=None, reference_image=None,
                 verbose=1):
        super().__init__(verbose)
        self._seconds = seconds
        self.callbacks = [
            cbks.ProgressCallback(),
            SaveIters(outdir=outdir),
            (tb_cbk := TensorBoard(logdir=outdir, transverse_slice=transverse_slice, coronal_slice=coronal_slice))]

        if reference_image:
            roi_image_dict = {f'S{i}': STIR.ImageData(f'S{i}.hv') for i in range(1, 8)}
            # NB: these metrics are for testing only.
            # The final evaluation will use metrics described in https://github.com/SyneRBI/PETRIC/wiki
            self.callbacks.append(
                ImageQualityCallback(
                    reference_image, tb_cbk.tb, roi_mask_dict=roi_image_dict, metrics_dict={
                        'MSE': mean_squared_error, 'MAE': self.mean_absolute_error, 'PSNR': peak_signal_noise_ratio},
                    statistics_dict={'MEAN': np.mean, 'STDDEV': np.std, 'MAX': np.max}))
        self.reset()

    def reset(self, seconds=None):
        self.limit = time() + (self._seconds if seconds is None else seconds)

    def __call__(self, algorithm: Algorithm):
        if (now := time()) > self.limit:
            log.warning("Timeout reached. Stopping algorithm.")
            raise StopIteration
        if self.callbacks:
            for c in self.callbacks:
                c(algorithm)
            self.limit += time() - now

    @staticmethod
    def mean_absolute_error(y, x):
        return np.mean(np.abs(y, x))


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


Dataset = namedtuple('Dataset', ['acquired_data', 'additive_term', 'mult_factors', 'OSEM_image', 'prior', 'kappa'])


def get_data(srcdir=".", outdir=OUTDIR, sirf_verbosity=0):
    srcdir = Path(srcdir)
    outdir = Path(outdir)
    STIR.set_verbosity(sirf_verbosity)                # set to higher value to diagnose problems
    STIR.AcquisitionData.set_storage_scheme('memory') # needed for get_subsets()

    _ = STIR.MessageRedirector(str(outdir / 'info.txt'), str(outdir / 'warnings.txt'), str(outdir / 'errors.txt'))
    acquired_data = STIR.AcquisitionData(str(srcdir / 'prompts.hs'))
    additive_term = STIR.AcquisitionData(str(srcdir / 'additive_term.hs'))
    mult_factors = STIR.AcquisitionData(str(srcdir / 'mult_factors.hs'))
    OSEM_image = STIR.ImageData(str(srcdir / 'OSEM_image.hv'))
    kappa = STIR.ImageData(str(srcdir / 'kappa.hv'))
    if (penalty_strength_file := (srcdir / 'penalisation_factor.txt')).is_file():
        penalty_strength = float(np.loadtxt(penalty_strength_file))
    else:
        penalty_strength = 1 / 700 # default choice
    prior = construct_RDP(penalty_strength, OSEM_image, kappa)

    return Dataset(acquired_data, additive_term, mult_factors, OSEM_image, prior, kappa)


if SRCDIR.is_dir():
    data_dirs_metrics = [(SRCDIR / "Siemens_mMR_NEMA_IQ", OUTDIR / "mMR_NEMA",
                          [MetricsWithTimeout(outdir=OUTDIR / "mMR_NEMA", transverse_slice=72, coronal_slice=109)]),
                         (SRCDIR / "NeuroLF_Hoffman_Dataset", OUTDIR / "NeuroLF_Hoffman",
                          [MetricsWithTimeout(outdir=OUTDIR / "NeuroLF_Hoffman", transverse_slice=72)]),
                         (SRCDIR / "Siemens_Vision600_thorax", OUTDIR / "Vision600_thorax",
                          [MetricsWithTimeout(outdir=OUTDIR / "Vision600_thorax")])]
else:
    log.warning("Source directory does not exist: %s", SRCDIR)
    data_dirs_metrics = [(None, None, [])]

if __name__ != "__main__":
    srcdir, outdir, metrics = data_dirs_metrics[0]
    if srcdir is None:
        data = None
    else:
        data = get_data(srcdir=srcdir, outdir=outdir)
        metrics[0].reset()
else:
    from docopt import docopt
    args = docopt(__doc__)
    logging.basicConfig(level=getattr(logging, args["--log"].upper()))
    from main import Submission, submission_callbacks
    assert issubclass(Submission, Algorithm)
    for srcdir, outdir, metrics in data_dirs_metrics:
        data = get_data(srcdir=srcdir, outdir=outdir)
        metrics[0].reset() # timeout from now
        algo = Submission(data)
        try:
            algo.run(np.inf, callbacks=metrics + submission_callbacks)
        except Exception as exc:
            print(exc)
        finally:
            del algo
