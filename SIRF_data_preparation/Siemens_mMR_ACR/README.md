# Files for preparation of ACR data
ugly and temporary

Steps to follow:
1. `python SIRF_data_preparation/Siemens_mMR_ACR/download.py`
2. `python SIRF_data_preparation/Siemens_mMR_ACR/prepare.py` (As there is no useful mumap, this will **not** do attenuation and scatter estimation)
3. `python SIRF_data_preparation.create_initial_images data/Siemens_mMR_ACR/final --template_image=None` (Reconstruct at full FOV size)
4. `mv data/Siemens_mMR_ACR/final/OSEM_image.* data/Siemens_mMR_ACR/processing` (this is really an NAC image and ideally would be renamed)
5. `python SIRF_data_preparation/Siemens_mMR_ACR/register_mumap.py` (output is orgdata/Siemens_mMR_ACR/processing/reg_mumap.hv etc)
6. However, registration failed, so this needs a manual intervention step:
   a. send data to Pawel who registers.
   b. Download from https://drive.google.com/file/d/13eGUL3fwdpCiWLjoP1Lhkd8xQOyV_AAZ/view?usp=sharing
   c. `cd  data/Siemens_mMR_ACR; unzip ../downloads/ACR_STIR_output.zip`
   d. copy data and rename (currently using `stir_math` executable here)
      ```sh
      stir_math orgdata/Siemens_mMR_ACR/processing/reg_mumap.hv   orgdata/Siemens_mMR_ACR/output/acr-mumap-complete.nii.gz
      ```
   e. uncompress .gz VOI files as STIR isn't happy with them (probably not necessary)
      ```sh
      for f in orgdata/Siemens_mMR_ACR/output/sampling_masks/*gz; do gunzip $f; done
      ```
6. Add hardware-mumap
   ```sh
   stir_math --accumulate  orgdata/Siemens_mMR_ACR/processing/reg_mumap.hv  orgdata/Siemens_mMR_ACR/output/ACR_hardware-to-STIR.nii.gz
   ```
7. 11. `python SIRF_data_preparation/run_OSEM.py Siemens_mMR_ACR`--end 200` (As there is now a useful mumap, this will now do attenuation and scatter estimation)
8. `python -m SIRF_data_preparation.create_initial_images data/Siemens_mMR_ACR --template_image=../../orgdata/Siemens_mMR_ACR/output/sampling_masks/acr-all-sampling-0-2mm_dipy.nii`
9. `python -m SIRF_data_preparation.data_QC --srcdir='data/Siemens_mMR_ACR' --transverse_slice=99`
10. edit `petric.py` and `SIRF_data_preparation/dataset_settings.py` for subsets etc. edit `OSEM_image.hv` to add modality, radionuclide and duration info which got lost.
11. `python SIRF_data_preparation/Siemens_mMR_ACR/VOI_prep.py`
12. `python SIRF_data_preparation/run_OSEM.py Siemens_mMR_ACR`
13. `python SIRF_data_preparation/run_BSREM.py Siemens_mMR_ACR`
