import os
import sys
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(os.path.dirname(this_directory))
sys.path.append(os.path.join(repo_directory, 'lib'))

import importlib
pet = importlib.import_module('sirf.STIR')

from sirf.Utilities import examples_data_path
from sirf_exercises import exercises_data_path
from sirf_exercises import prepare_challenge_data

# brutal support to add some parameters to the script
start = 0
end = 600
if len(sys.argv) > 1:
    start = float(sys.argv[1])
if len(sys.argv) > 2:
    end = float(sys.argv[2])

data_path = exercises_data_path('PET', 'mMR', 'NEMA_IQ')
sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')
challenge_data_path = os.path.join(repo_directory, 'data')
intermediate_data_path = os.path.join(challenge_data_path, 'intermediate')
os.makedirs(challenge_data_path, exist_ok=True)
os.chdir(challenge_data_path)
os.makedirs(intermediate_data_path, exist_ok=True)

prepare_challenge_data(data_path, sirf_data_path, challenge_data_path, intermediate_data_path, '20170809_NEMA_',
    '60min_UCL.l.hdr', 'MUMAP_UCL.v', 'MUMAP_UCL.hv', 'UCL.n', 'norm.n.hdr', 'mMR_template_span11_small.hs',
    'prompts', 'multfactors', 'additive', 'randoms',
    'attenuation_factor', 'attenuation_correction_factor', 'scatter', start, end)

