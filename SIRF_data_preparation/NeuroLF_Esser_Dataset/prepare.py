import os

import sirf.STIR as STIR
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path

# %% set paths filenames
scanID = 'NeuroLF_Esser_Dataset'
intermediate_data_path = the_orgdata_path(scanID, 'processing')
orgdata_path = the_orgdata_path(scanID, scanID)
os.makedirs(intermediate_data_path, exist_ok=True)
data_path = the_data_path(scanID)
os.makedirs(data_path, exist_ok=True)
# %%
acquired_data = STIR.AcquisitionData(os.path.join(orgdata_path, 'neuroLF_prompts.hs'))
norm_factors = STIR.AcquisitionData(os.path.join(orgdata_path, 'neuroLF_normalisation_factors.hs'))
randoms = STIR.AcquisitionData(os.path.join(orgdata_path, 'neuroLF_random.hs'))
scatter = STIR.AcquisitionData(os.path.join(orgdata_path, 'neuroLF_scatter.hs'))
acfs = STIR.AcquisitionData(os.path.join(orgdata_path, 'neuroLF_acfs.hs'))

# %%
mult_factors = (acfs * norm_factors).power(-1.)
additive_term = (scatter+randoms) * norm_factors
acquired_data.write(os.path.join(data_path, 'prompts.hs'))
mult_factors.write(os.path.join(data_path, 'mult_factors.hs'))
additive_term.write(os.path.join(data_path, 'additive_term.hs'))
