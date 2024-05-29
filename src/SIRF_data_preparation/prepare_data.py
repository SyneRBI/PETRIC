import os
import sys
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(os.path.dirname(this_directory))
sys.path.append(os.path.join(repo_directory, 'lib'))

import importlib
pet = importlib.import_module('sirf.STIR')

from sirf.Utilities import examples_data_path
from sirf_exercises import exercises_data_path

def fix_siemens_norm_EOL(in_filename, out_filename):
    with open(in_filename, mode="rb") as f:
        data = bytearray(f.read())
    for i in range(len(data)):
        if data[i] == 13: #'\r'
            data[i] = 10 # \n
    with open(out_filename, mode="wb") as f:
        f.write(data)


data_path = exercises_data_path('PET', 'mMR', 'NEMA_IQ')
sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')
challenge_data_path = os.path.join(repo_directory, 'data')
os.makedirs(challenge_data_path, exist_ok=True)

f_template = os.path.join(sirf_data_path, 'mMR_template_span11_small.hs')

f_listmode = os.path.join(data_path, '20170809_NEMA_60min_UCL.l.hdr')
siemens_attn_header = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v.hdr')
siemens_attn_image = os.path.join(data_path, '20170809_NEMA_MUMAP_UCL.v')
siemens_norm_header = os.path.join(data_path, '20170809_NEMA_UCL.n.hdr')
siemens_norm = os.path.join(data_path, '20170809_NEMA_UCL.n')

stir_norm_header = os.path.join(challenge_data_path, 'norm.n.hdr')
stir_attn_header = os.path.join(challenge_data_path, '20170809_NEMA_MUMAP_UCL.hv')
f_prompts = os.path.join(challenge_data_path, 'prompts')
f_randoms = os.path.join(challenge_data_path, 'randoms')

os.system('cp ' + siemens_attn_image + ' ' + challenge_data_path)
os.system('convertSiemensInterfileToSTIR.sh ' + siemens_attn_header + ' ' + stir_attn_header)

os.system('cp ' + siemens_norm + ' ' + challenge_data_path)

fix_siemens_norm_EOL(siemens_norm_header, stir_norm_header)

# engine's messages go to files, except error messages, which go to stdout
_ = pet.MessageRedirector('info.txt', 'warn.txt')

# select acquisition data storage scheme
pet.AcquisitionData.set_storage_scheme('memory')

# read acquisition data template
acq_data_template = pet.AcquisitionData(f_template)

listmode_data = pet.ListmodeData(f_listmode)

# create listmode-to-sinograms converter object
lm2sino = pet.ListmodeToSinograms()

prompts, randoms = lm2sino.prompts_and_randoms_from_listmode(listmode_data, 0, 10, acq_data_template)
print('data shape: %s' % repr(prompts.shape))
print('prompts norm: %f' % prompts.norm())
print('randoms norm: %f' % randoms.norm())
prompts.write(f_prompts)
randoms.write(f_randoms)

attn_image = pet.ImageData(stir_attn_header)
attn, af, acf = pet.AcquisitionSensitivityModel.compute_attenuation_factors(prompts, attn_image)
print('norm of the attenuation factor: %f' % af.norm())
print('norm of the attenuation correction factor: %f' % acf.norm())

asm = pet.AcquisitionSensitivityModel(stir_norm_header)
se = pet.ScatterEstimator()
se.set_input(prompts)
se.set_attenuation_image(attn_image)
se.set_randoms(randoms)
se.set_asm(asm)
se.set_attenuation_correction_factors(acf)
se.set_num_iterations(4)
se.set_OSEM_num_subsets(7)
se.set_output_prefix("scatter")
se.set_up()
se.process()
scatter = se.get_output()
print('norm of the scatter estimate: %f' % scatter.norm())

multfact = af.clone()
asm.set_up(af)
asm.unnormalise(multfact)
print(multfact.norm())

background = randoms + scatter
print('norm of the backgrount term: %f' % background.norm())

asm_mf = pet.AcquisitionSensitivityModel(multfact)
asm_mf.set_up(background)
asm_mf.normalise(background)
print('norm of the additive term: %f' % background.norm())

