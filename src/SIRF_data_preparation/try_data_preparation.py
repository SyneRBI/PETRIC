import os
import data_preparation_setup
from data_preparation_setup import repo_directory
from data_preparation_setup import sinograms_and_randoms_from_listmode
from sirf_exercises import exercises_data_path
from sirf.Utilities import examples_data_path

data_path = exercises_data_path('PET', 'mMR', 'NEMA_IQ')
#challenge_data_path = os.path.join(repo_directory, 'data')
challenge_data_path = os.path.join(repo_directory, 'tmp')

listmode_filename = os.path.join(data_path, '20170809_NEMA_60min_UCL.l.hdr')
template_filename = os.path.join(examples_data_path('PET'), 'mMR', 'mMR_template_span11_small.hs')
sinograms_filename = 'sinograms'
randoms_filename = 'randoms'
sinograms_and_randoms_from_listmode(listmode_filename, (0, 10), template_filename, \
challenge_data_path, sinograms_filename, randoms_filename)
