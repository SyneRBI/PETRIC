import os
import data_preparation_setup
from data_preparation_setup import repo_directory
from data_preparation_setup import sinograms_and_randoms_from_listmode
from data_preparation_setup import acquisition_sensitivity_from_attenuation
from sirf_exercises import exercises_data_path
from sirf.Utilities import examples_data_path

data_path = '.'
# challenge_data_path = os.path.join(repo_directory, 'data')
# for debugging purposes using tmp1 subfolder instead of data
challenge_data_path = './tmpl'

listmode_filename = os.path.join(data_path, '20170809_NEMA_60min_UCL.l.hdr')
template_filename = os.path.join(examples_data_path('PET'), 'mMR', 'mMR_template_span11_small.hs')
sinograms_filename = 'sinograms'
randoms_filename = 'randoms'
sinograms_and_randoms_from_listmode(listmode_filename, (0, 10), template_filename, \
challenge_data_path, sinograms_filename, randoms_filename)

siemens_attn_header = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v.hdr')
siemens_attn_image = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v')
stir_attn_header = os.path.join(challenge_data_path, '20170809_NEMA_MUMAP_UCL.hv')
acq_sens_filename = os.path.join(challenge_data_path, 'acf.hs')
os.system('cp ' + siemens_attn_image + ' ' + challenge_data_path)
acquisition_sensitivity_from_attenuation(siemens_attn_header, template_filename, stir_attn_header, acq_sens_filename)

siemens_norm = os.path.join(data_path, '20170809_NEMA_UCL.n')
os.system('cp ' + siemens_norm + ' ' + challenge_data_path)
siemens_norm_header = os.path.join(data_path, '20170809_NEMA_UCL.n.hdr')
os.system('cp ' + siemens_norm_header + ' ' + challenge_data_path)
stir_norm_header = os.path.join(challenge_data_path, 'norm.n.hdr')
os.system('cp ' + siemens_norm_header + ' ' + stir_norm_header)
# cmd = 'sed -i.bak "s/\r\([^\n]\)/\r\n\1/g" norm.n.hdr'
# fails with the error message
# sed: -e expression #1, char 7: unterminated `s' command
