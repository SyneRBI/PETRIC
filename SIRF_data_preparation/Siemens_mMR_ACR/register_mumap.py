import os
import sys
import sirf.STIR as STIR
import sirf.Reg as Reg
#%%
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(this_directory)
sys.path.append(repo_directory)
repo_directory = os.path.dirname(repo_directory)
# %% set paths filenames
root_path = os.path.join(repo_directory, 'data', 'Siemens_mMR_ACR')
intermediate_data_path = os.path.join(root_path, 'processing')
output_path = os.path.join(root_path, 'final')
mumap_filename = os.path.join(root_path, 'ACR_data_design/synth_mumap/acr-complete-umap.nii.gz')
# %% write current OSEM image as Nifti
NAC_image = STIR.ImageData(os.path.join(intermediate_data_path, 'OSEM_image.hv'))
NAC_image_filename = os.path.join(intermediate_data_path, 'NAC_image.nii')
NAC_image.write_par(NAC_image_filename, os.path.join(STIR.get_STIR_examples_dir(), 'samples', 'stir_math_ITK_output_file_format.par'))
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
reg.get_output(0).write(reg_mumap_filename + '.nii')
# %% write as Interfile
reg_mumap=STIR.ImageData(reg_mumap_filename_nii)
reg_mumap.write(reg_mumap_filename + '.hv')
