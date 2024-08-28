import os

import sirf.Reg as Reg
import sirf.STIR as STIR
from SIRF_data_preparation.data_utilities import the_orgdata_path

# %% set paths filenames
scanID = 'Siemens_mMR_ACR'
intermediate_data_path = the_orgdata_path(scanID, 'processing')
mumap_filename = the_orgdata_path(scanID, 'ACR_data_design/synth_mumap/acr-complete-umap.nii.gz')
# %% write current OSEM image as Nifti
NAC_image = STIR.ImageData(os.path.join(intermediate_data_path, 'OSEM_image.hv'))
NAC_image_filename = os.path.join(intermediate_data_path, 'NAC_image.nii')
NAC_image.write_par(NAC_image_filename,
                    os.path.join(STIR.get_STIR_examples_dir(), 'samples', 'stir_math_ITK_output_file_format.par'))
# %% read as Reg.ImageData
NAC_image = Reg.ImageData(NAC_image_filename)
mumap = Reg.ImageData(mumap_filename)
# %% register mu-map to NAC
reg = Reg.NiftyAladinSym()
reg.set_reference_image(NAC_image)
reg.add_floating_image(mumap)
reg.process()
# %% write as Nifti
reg_mumap_filename = os.path.join(intermediate_data_path, 'reg_mumap')
reg_mumap_filename_nii = reg_mumap_filename + '.nii'
reg.get_output(0).write(reg_mumap_filename_nii)
# %% write as Interfile
reg_mumap = STIR.ImageData(reg_mumap_filename_nii)
reg_mumap.write(reg_mumap_filename + '.hv')
