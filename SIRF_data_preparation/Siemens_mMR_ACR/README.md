# Files for preparation of ACR data
ugly and temporary

Steps to follow:
1. `python SIRF_data_preparation/Siemens_mMR_ACR/download.py`
2. `python SIRF_data_preparation/Siemens_mMR_ACR/prepare.py` (As there is no useful mumap, this will **not** do attenuation and scatter estimation)
3. `python SIRF_data_preparation/create_initial_images.py data/Siemens_mMR_ACR/final --template-image=None` (Reconstruct at full FOV size)
4. `mv data/Siemens_mMR_ACR/final/OSEM_image.* data/Siemens_mMR_ACR/processing` (this is really an NAC image)
5. `python SIRF_data_preparation/Siemens_mMR_ACR/register_mumap.py` (output is data/Siemens_mMR_ACR/processing/reg_mumap.hv etc)
6. `python SIRF_data_preparation/Siemens_mMR_ACR/prepare.py --end 200` (As there is now a useful mumap, this will now do attenuation and scatter estimation)
7. `python SIRF_data_preparation/create_initial_images.py -s 200 data/Siemens_mMR_ACR/final` (ideally add `--template-image some_VOI`)
However, registration failed, so this needs a manual intervention step. Output of that should be data/Siemens_mMR_ACR/processing/reg_mumap.hv
