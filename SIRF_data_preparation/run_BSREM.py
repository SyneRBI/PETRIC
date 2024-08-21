"""Run BSREM for PETRIC

Usage:
  run_BSREM.py <data_set> [--help | options]

Arguments:
  <data_set>  path to data files as well as prefix to use

"""
# Copyright 2024 Rutherford Appleton Laboratory STFC
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.1.0'

import logging
import math
import os

from docopt import docopt

from petric import MetricsWithTimeout, get_data, SRCDIR, OUTDIR
from SIRF_data_preparation.dataset_settings import get_settings
from pathlib import Path

from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.partitioner import partitioner

import SIRF_data_preparation.data_QC as data_QC
import matplotlib.pyplot as plt
#%%
args = docopt(__doc__, argv=None, version=__version__)
#logging.basicConfig(level=logging.INFO)

scanID = args['<data_set>']

if not all((SRCDIR.is_dir(), OUTDIR.is_dir())):
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
    OUTDIR = PETRICDIR / 'output'

outdir = OUTDIR/ scanID / "BSREM"
srcdir = SRCDIR / scanID
#log.info("Finding files in %s", srcdir)

settings = get_settings(scanID)

data = get_data(srcdir=srcdir, outdir=outdir)
data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term, data.mult_factors,
                                                            settings.num_subsets, mode="staggered",
                                                            initial_image=data.OSEM_image)
# WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
data.prior.set_penalisation_factor(data.prior.get_penalisation_factor() / len(obj_funs))
data.prior.set_up(data.OSEM_image)
for f in obj_funs: # add prior evenly to every objective function
    f.set_prior(data.prior)

algo = BSREM1(data_sub, obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01,
              update_objective_interval=80)
#%%
algo.run(15000, callbacks=[MetricsWithTimeout(**settings.slices, outdir=outdir, seconds=3600*100)])
#%%
fig = plt.figure()
data_QC.plot_image(algo.get_output(), **settings.slices)
fig.savefig(outdir / "BSREM_slices.png")
#plt.show()
