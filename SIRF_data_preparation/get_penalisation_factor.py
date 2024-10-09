#!/usr/bin/env python
"""Find penalisation factor for one dataset based on another

Usage:
  get_penalisation_factor.py [--help | options]

Options:
  -h, --help
  --dataset=<name>                 dataset name (required)
  --ref_dataset=<name>             reference dataset name (required)
  -w, --write_penalisation_factor  write in data/<dataset>/penalisation_factor.txt
"""

# Copyright 2024 University College London
# Licence: Apache-2.0

import sys
from pathlib import Path

import numpy as np
from docopt import docopt

# %% imports
import sirf.STIR
from petric import Dataset, get_data
from SIRF_data_preparation.data_utilities import the_data_path

# %%
__version__ = "0.1.0"

write_penalisation_factor = False
if "ipykernel" not in sys.argv[0]: # clunky way to be able to set variables from within jupyter/VScode without docopt
    args = docopt(__doc__, argv=None, version=__version__)

    # logging.basicConfig(level=logging.INFO)

    dataset = args["--dataset"]
    ref_dataset = args["--ref_dataset"]
    if dataset is None or ref_dataset is None:
        print("Need to set the --dataset arguments")
        exit(1)
    write_penalisation_factor = args["--write_penalisation_factor"]

else:         # set it by hand, e.g.
    ref_dataset = "NeuroLF_Hoffman_Dataset"
    dataset = "Siemens_mMR_NEMA_IQ"
    write_penalisation_factor = True


# %%
def VOImean(im: sirf.STIR.ImageData, background_mask: sirf.STIR.ImageData) -> float:
    background_indices = np.where(background_mask.as_array())
    return np.mean(im.as_array()[background_indices]) / len(background_indices)


def backgroundVOImean(dataset: Path) -> float:
    im = sirf.STIR.ImageData(str(dataset / "OSEM_image.hv"))
    VOI = sirf.STIR.ImageData(str(dataset / "PETRIC" / "VOI_background.hv"))
    return VOImean(im, VOI)


def get_penalisation_factor(ref_data: Dataset, cur_data: Dataset) -> float:
    ref_mean = VOImean(ref_data.OSEM_image, ref_data.background_mask)
    cur_mean = VOImean(cur_data.OSEM_image, cur_data.background_mask)
    print(f"ref_mean={ref_mean}, cur_mean={cur_mean}, c/r={cur_mean / ref_mean}, r/c={ref_mean / cur_mean}")
    ref_penalisation_factor = ref_data.prior.get_penalisation_factor()
    penalisation_factor = ref_penalisation_factor * cur_mean / ref_mean
    print(f"penalisation_factor={penalisation_factor}")
    return penalisation_factor


# %%
refdir = Path(the_data_path(ref_dataset))
curdir = Path(the_data_path(dataset))
# %%
ref_data = get_data(refdir, outdir=None)
cur_data = get_data(curdir, outdir=None)
# %%
penalisation_factor = get_penalisation_factor(ref_data, cur_data)

# %%
if write_penalisation_factor:
    filename = curdir / "penalisation_factor.txt"
    print(f"Writing it to {filename}")
    with open(filename, "w") as file:
        file.write(str(penalisation_factor))
