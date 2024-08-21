# Functions/classes for PETRIC

## Utility functions to prepare data for the Challenge

Participants should never have to use these (unless you want to create your own dataset).

- `create_initial_images.py`: functions+script to run OSEM and compute the "kappa" image from existing data
- `data_QC.py`: generates plots for QC
- `plot_BSREM_metrics.py`: plot objective functions/metrics after a BSREM run
- `run_BSREM.py` and `run_OSEM.py`: scripts to run these algorithms for a dataset

## Helpers

- `data_utilities.py`: functions to use sirf.STIR to output prompts/mult_factors and additive_term
  and handle Siemens data
- `evaluation_utilities.py`: reading/plotting helpers for values of the objective function and metrics
- `PET_plot_functions.py`: plotting helpers
- `dataset_settings.py`: settings for display of good slices, subsets etc

## Sub-folders per data-set

These contain files specific to the data-set, e.g. for downloading, VOI conversion, settings used for recon, etc.
Warning: this will be messy, and might be specific to whoever prepared this data-set. For instance,
for the Siemens mMR NEMA IQ data (on Zenodo):
- `download_Siemens_mMR_NEMA_IQ.py`: download and extract
- `prepare_mMR_NEMA_IQ_data.py`: prepare the data (prompts etc)
- `BSREM_*.py`: functions with specific settings for a particular data-set
