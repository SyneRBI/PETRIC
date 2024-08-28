# %%
import os
import shutil
import subprocess
from zipfile import ZipFile

from zenodo_get import zenodo_get

from sirf.Utilities import examples_data_path

# %%
from SIRF_data_preparation.data_utilities import the_data_path

sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')

# %% set paths
download_path = the_data_path('downloads')
os.makedirs(download_path, exist_ok=True)

dest_path = the_data_path('Siemens_mMR_ACR')
os.makedirs(dest_path, exist_ok=True)
print('dest path: %s' % dest_path)
processing_path = os.path.join(dest_path, 'processing')
os.makedirs(processing_path, exist_ok=True)
print('processing path: %s' % processing_path)
# %% Download from Zenodo
record = '5760092'
download_path = os.path.join(download_path, record)
print('zenodo_get -r ' + record + ' -o ' + download_path)
zenodo_get(['-r', record, '-o', download_path])
# %% extract from zip
file = ZipFile(os.path.join(download_path, 'ACR_data_design.zip'))
file.extractall(dest_path)
# %% extract from dcm
subprocess.run([
    'nm_extract', '-i',
    os.path.join(dest_path, 'ACR_data_design', 'raw', 'list.dcm'), '-o', processing_path])
subprocess.run([
    'nm_extract', '-i',
    os.path.join(dest_path, 'ACR_data_design', 'raw', 'norm.dcm'), '-o', processing_path])
# %% copy template for SIRF
f_template = os.path.join(sirf_data_path, 'mMR_template_span11')
shutil.copy(f_template + '.hs', processing_path)
shutil.copy(f_template + '.s', processing_path)
# %%
print('done')
