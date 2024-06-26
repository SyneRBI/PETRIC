import os
import shutil
from zipfile import ZipFile

from zenodo_get import zenodo_get

from sirf.Utilities import examples_data_path

sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(this_directory)
challenge_data_path = os.path.join(repo_directory, 'data')
print('SIRF data path: %s' % sirf_data_path)
print('Challenge24 data path: %s' % challenge_data_path)

dest_path = os.path.join(challenge_data_path, 'Siemens_mMR_NEMA_IQ', 'raw')
os.makedirs(dest_path, exist_ok=True)

record = '1304454'
download_path = os.path.join(challenge_data_path, 'downloads', record)
os.makedirs(download_path, exist_ok=True)

print('downloading Siemens mMR NEMA_IQ data, please wait...')
print('zenodo_get -r ' + record + ' -o ' + download_path)
zenodo_get(['-r', record, '-o', download_path])
file = ZipFile(os.path.join(download_path, 'NEMA_IQ.zip'))
file.extractall(dest_path)
f_template = os.path.join(sirf_data_path, 'mMR_template_span11')
shutil.copy(f_template + '.hs', os.path.join(dest_path, 'NEMA_IQ'))
shutil.copy(f_template + '.s', os.path.join(dest_path, 'NEMA_IQ'))
print('done')
