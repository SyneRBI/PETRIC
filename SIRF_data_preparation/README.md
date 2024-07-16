# Functions/classes for PETRIC

## Functions to create images that are provided to participants

- `create_initial_images.py`: functions+script to run OSEM and compute the "kappa" image from existing data
- `BSREM_common.py`: functions to run BSREM with various callbacks
- `BSREM_*.py`: functions with specific settings for a particular data-set

## Utility functions to prepare data for the Challenge

Participants should never have to use these (unless you want to create your own dataset).

- `data_utilities.py`: functions to use sirf.STIR to output prompts/mult_factors and additive_term
  and handle Siemens data
- `data_QC.py`: generates plots for QC
- Siemens mMR NEMA IQ data (on Zenodo)
  - `download_Siemens_mMR_NEMA_IQ.py`: download and extract
  - `prepare_mMR_NEMA_IQ_data.py`: prepare the data (prompts etc)

## Helpers

- `evaluation_utilities.py`: reading/plotting helpers for values of the objective function and metrics
- `PET_plot_functions.py`: plotting helpers
