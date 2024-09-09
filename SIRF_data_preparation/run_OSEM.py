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

from pathlib import Path

import matplotlib.pyplot as plt
from docopt import docopt

import main_OSEM
from petric import OUTDIR, SRCDIR, MetricsWithTimeout, get_data
from SIRF_data_preparation import data_QC
from SIRF_data_preparation.dataset_settings import get_settings

# %%
args = docopt(__doc__, argv=None, version=__version__)
# logging.basicConfig(level=logging.INFO)

scanID = args['<data_set>']

if not all((SRCDIR.is_dir(), OUTDIR.is_dir())):
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
    OUTDIR = PETRICDIR / 'output'

outdir = OUTDIR / scanID / "OSEM"
srcdir = SRCDIR / scanID
# log.info("Finding files in %s", srcdir)

settings = get_settings(scanID)

data = get_data(srcdir=srcdir, outdir=outdir)
# %%
algo = main_OSEM.Submission(data, settings.num_subsets, update_objective_interval=20)
algo.run(400, callbacks=[MetricsWithTimeout(**settings.slices, seconds=5000, outdir=outdir)])
# %%
fig = plt.figure()
data_QC.plot_image(algo.get_output(), **settings.slices)
fig.savefig(outdir / "OSEM_slices.png")
# plt.show()
