import os
import data_preparation_setup
from data_preparation_setup import repo_directory
from data_preparation_setup import sinograms_and_randoms_from_listmode
from data_preparation_setup import acquisition_sensitivity_from_attenuation
from data_preparation_setup import fix_siemens_norm_EOL
from data_preparation_setup import estimate_scatter
from data_preparation_setup import create_multfactors
from data_preparation_setup import create_background_and_additive
from sirf.Utilities import examples_data_path

data_path = '.'
# challenge_data_path = os.path.join(repo_directory, 'data')
# for debugging purposes using tmp1 subfolder instead of data
challenge_data_path = './tmpl'
os.makedirs(challenge_data_path, exist_ok = True)

listmode_filename = os.path.join(data_path, '20170809_NEMA_60min_UCL.l.hdr')
template_filename = os.path.join(examples_data_path('PET'), 'mMR', 'mMR_template_span11_small.hs')
sinograms_filename = 'prompts'
randoms_filename = 'randoms'
sinograms_filename = os.path.join(challenge_data_path, sinograms_filename)
randoms_filename = os.path.join(challenge_data_path, randoms_filename)

sinograms_and_randoms_from_listmode(listmode_filename, (0, 600), template_filename,
                                    sinograms_filename, randoms_filename)
sinograms_filename += '.hs'
randoms_filename += '.hs'

siemens_attn_header = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v.hdr')
siemens_attn_image = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v')
stir_attn_header = os.path.join(challenge_data_path, '20170809_NEMA_MUMAP_UCL.hv')
ac_sens_filename = os.path.join(challenge_data_path, 'ac_factors.hs')
os.system('cp ' + siemens_attn_image + ' ' + challenge_data_path)
ac_factors = acquisition_sensitivity_from_attenuation(siemens_attn_header, sinograms_filename, stir_attn_header, ac_sens_filename)

siemens_norm = os.path.join(data_path, '20170809_NEMA_UCL.n')
os.system('cp ' + siemens_norm + ' ' + challenge_data_path)
siemens_norm_header = os.path.join(data_path, '20170809_NEMA_UCL.n.hdr')
stir_norm_header = os.path.join(challenge_data_path, 'norm.n.hdr')
fix_siemens_norm_EOL(siemens_norm_header, stir_norm_header)

scatter_filename = os.path.join(challenge_data_path, "scatter")
estimate_scatter(sinograms_filename, randoms_filename, stir_norm_header, stir_attn_header, ac_factors, scatter_filename)
scatter_filename += '.hs'

mult_factors_filename = os.path.join(challenge_data_path, "mult_factors.hs")
mult_factors = create_multfactors(stir_norm_header, ac_factors, mult_factors_filename)

background_filename = os.path.join(challenge_data_path, "background.hs")
additive_term_filename = os.path.join(challenge_data_path, "additive_term.hs")
create_background_and_additive(randoms_filename, scatter_filename,  mult_factors, background_filename, additive_term_filename)
