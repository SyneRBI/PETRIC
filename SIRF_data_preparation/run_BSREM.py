"""Run BSREM for PETRIC

Usage:
  run_BSREM.py <data_set> [--help | options]

Arguments:
  <data_set>     path to data files as well as prefix to use (e.g. Siemens_mMR_NEMA_EQ)

Options:
  --updates=<u>               number of updates to run [default: 15000]
  --initial_image=<filename>  optional initial image, normally the OSEM_image. If specified,
                              output will be in BSREM_cont.
  --initial_step_size=<s>     start stepsize [default: .3]
  --relaxation_eta=<r>        relaxation factor per epoch [default: .01]
"""
# Copyright 2024 Rutherford Appleton Laboratory STFC
# Copyright 2024 University College London
# Licence: Apache-2.0
__version__ = '0.3.0'

from pathlib import Path

import matplotlib.pyplot as plt
from docopt import docopt

import sirf.STIR as STIR
from petric import OUTDIR, SRCDIR, MetricsWithTimeout, get_data
from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.partitioner import partitioner
from SIRF_data_preparation import data_QC
from SIRF_data_preparation.dataset_settings import get_settings

# %%
args = docopt(__doc__, argv=None, version=__version__)
# logging.basicConfig(level=logging.INFO)

scanID = args['<data_set>']
num_updates = int(args['--updates'])
initial_image = args['--initial_image']
initial_step_size = float(args['--initial_step_size'])
relaxation_eta = float(args['--relaxation_eta'])

if not all((SRCDIR.is_dir(), OUTDIR.is_dir())):
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
    OUTDIR = PETRICDIR / 'output'

outdir = OUTDIR / scanID
srcdir = SRCDIR / scanID
# log.info("Finding files in %s", srcdir)

settings = get_settings(scanID)

data = get_data(srcdir=srcdir, outdir=outdir)
if initial_image is None:
    initial_image = data.OSEM_image
    outdir = outdir / "BSREM"
else:
    initial_image = STIR.ImageData(initial_image)
    outdir = outdir / "BSREM_cont"

print("Penalisation factor:", data.prior.get_penalisation_factor())
print("num_subsets:", settings.num_subsets)
print("num_updates:", num_updates)
print("initial_image:", initial_image)
print("outdir:", outdir)
print("initial_step_size:", initial_step_size)
print("relaxation_eta:", relaxation_eta)

data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term, data.mult_factors,
                                                            settings.num_subsets, mode="staggered",
                                                            initial_image=data.OSEM_image)
# WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
data.prior.set_penalisation_factor(data.prior.get_penalisation_factor() / len(obj_funs))
data.prior.set_up(data.OSEM_image)
for f in obj_funs: # add prior evenly to every objective function
    f.set_prior(data.prior)

algo = BSREM1(data_sub, obj_funs, initial=initial_image, initial_step_size=initial_step_size,
              relaxation_eta=relaxation_eta, update_objective_interval=80)
# %%
algo.run(num_updates, callbacks=[MetricsWithTimeout(**settings.slices, interval=80, outdir=outdir, seconds=3600 * 100)])
# %%
fig = plt.figure()
data_QC.plot_image(algo.get_output(), **settings.slices)
fig.savefig(outdir / "BSREM_slices.png")
# plt.show()
