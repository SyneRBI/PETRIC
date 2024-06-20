import os
import sys
from sirf.Utilities import examples_data_path

sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(this_directory)
challenge_data_path = os.path.join(repo_directory, 'data')
print('SIRF data path: %s' % sirf_data_path)
print('Challenge24 data path: %s' % challenge_data_path)

os.makedirs(challenge_data_path, exist_ok=True)
f_template = os.path.join(sirf_data_path, 'mMR_template_span11')
os.system('cp ' + f_template + '* ' + challenge_data_path)

print('downloading Siemens mMR NEMA_IQ data, please wait...')
print('zenodo_get -r 1304454 -o ' + challenge_data_path)
os.system('zenodo_get -r 1304454 -o ' + challenge_data_path)
os.system('unzip ' + challenge_data_path + '/NEMA_IQ.zip')
print('done')
