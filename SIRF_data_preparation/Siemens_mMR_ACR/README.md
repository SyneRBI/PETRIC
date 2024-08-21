# Files for preparation of ACR data
ugly and temporary

Steps to follow:
1. `python SIRF_data_preparation/Siemens_mMR_ACR/download.py`
2. `python SIRF_data_preparation/Siemens_mMR_ACR/prepare.py` (As there is no useful mumap, this will **not** do attenuation and scatter estimation)
3. `python SIRF_data_preparation/create_initial_images.py data/Siemens_mMR_ACR/final --template_image=None` (Reconstruct at full FOV size)
4. `mv data/Siemens_mMR_ACR/final/OSEM_image.* data/Siemens_mMR_ACR/processing` (this is really an NAC image and ideally would be renamed)
5. `python SIRF_data_preparation/Siemens_mMR_ACR/register_mumap.py` (output is data/Siemens_mMR_ACR/processing/reg_mumap.hv etc)
6. However, registration failed, so this needs a manual intervention step:
   a. send data to Pawel who registers.
   b. Download from https://drive.google.com/file/d/13eGUL3fwdpCiWLjoP1Lhkd8xQOyV_AAZ/view?usp=sharing
   c. `cd  data/Siemens_mMR_ACR; unzip ../downloads/ACR_STIR_output.zip`
   d. copy data and rename (currently using `stir_math` executable here)
      ```sh
      gunzip data/Siemens_mMR_ACR/output/acr-mumap-complete.nii.gz
      stir_math data/Siemens_mMR_ACR/processing/reg_mumap.hv   data/Siemens_mMR_ACR/output/acr-mumap-complete.nii
      ```
   e. uncompress .gz VOI files as STIR isn't happy with them
      ```sh
      for f in data/Siemens_mMR_ACR/output/sampling_masks/*gz; do gunzip $f; done
      ```
6. `python SIRF_data_preparation/Siemens_mMR_ACR/prepare.py --end 200` (As there is now a useful mumap, this will now do attenuation and scatter estimation)
7. `python SIRF_data_preparation/create_initial_images.py -s 200 data/Siemens_mMR_ACR/final --template_image=data/Siemens_mMR_ACR/output/sampling_masks/acr-all-sampling-0-2mm_dipy.nii`
8. ` python ~/devel/PETRIC/SIRF_data_preparation/data_QC.py --srcdir='data/Siemens_mMR_ACR/final' --transverse_slice=99`
