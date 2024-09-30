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

# Steps to follow to prepare data
If starting from Siemens mMR list-mode data and letting SIRF take care of scatter etc, check for instance [steps for Siemens mMR ACR](Siemens_mMR_ACR/README.md). If pre-prepared data are given, check that naming of all files is correct. KT normally puts all data
in `~/devel/PETRIC/data/<datasetname>` with `datasetname` following convention of `scanner_phantom-name` as others (instructions below and indeed some scripts might assume this location). Change working directory to where data sits and add PETRIC to your python-path, e.g.
```
PYTHONPATH=~/devel/PETRIC:$PYTHONPATH`
```

1. Run initial [data_QC.py](data_QC.py)
   ```
   python -m SIRF_data_preparation.data_QC
   ```

2. Run [create_initial_images.py](create_initial_images.py).
   ```
   python -m SIRF_data_preparation.create_initial_images --template_image=<some_image>
   ```
   where the template image is one of the given VOIs (it does not matter which one, as they should all have the same geometry). (If you need to create VOIs yourself, you can use `None` or the vendor image).
3. Edit `OSEM_image.hv` to add modality, radionuclide and duration info which got lost (copy from `prompts.hs`)
4. Edit [dataset_settings.py](dataset_settings.py) for subsets (used by our reference reconstructions only, not by participants).
5. Edit [petric.py](../petric.py) for slices to use for creating figures (`DATA_SLICES`). Note that `data_QC` outputs centre-of-mass of the VOIs, which can be helpful for this.
6. Run [data_QC.py](data_QC.py) which should now make more plots. Check VOI alignment etc.
   ```
   python -m SIRF_data_preparation.data_QC --dataset=<datasetname>
   ```
7. `cd ../..`
8. `python -m SIRF_data_preparation.run_OSEM <datasetname>`
9. `python -m SIRF_data_preparation.run_BSREM  <datasetname>`
10. Adapt [plot_BSREM_metrics.py](plot_BSREM_metrics.py) (probably only the `<datasetname>`) and run interactively.
11. Copy the BSREM ` iter_final` to `data/<datasetname>/PETRIC/reference_image`, e.g.
    ```
    stir_math data/<datasetname>/PETRIC/reference_image.hv output/<datasetname>/iter_final.hv
    ```
12. `cd data/<datasetname>; rm -f *ahv info.txt warnings.txt`, check its `README.md` etc
13. Transfer to web-server
