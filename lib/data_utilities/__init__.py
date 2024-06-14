'''Library of common utilities shared between notebooks in SIRF-Exercises.'''

# Author: Ashley Gillman
# Copyright 2021 Commonwealth Scientific and Industrial Research Organisation
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import importlib
pet = importlib.import_module('sirf.STIR')
import logging

logger = logging.getLogger("sirf_exercises")


def the_data_path(*data_type):
    '''
    Returns the path to data used by SIRF-exercises.

    data_type: either 'PET', 'MR' or 'Synergistic', or use multiple arguments for
    subdirectories like exercises_data_path('PET', 'mMR', 'NEMA_IQ').
    '''
    try:
        # from installer?
        from .data_path import data_path
    except ImportError:
        # from ENV variable?
        data_path = os.environ.get('SIRF_EXERCISES_DATA_PATH')

    if data_path is None or not os.path.exists(data_path):
        raise RuntimeError(
            "Exercises data weren't found. Please run download_data.sh in the "
            "scripts directory (use its -h option to get help)")

    return os.path.join(data_path, *data_type)

def fix_siemens_norm_EOL(in_filename, out_filename):
    with open(in_filename, mode="rb") as f:
        data = bytearray(f.read())
    for i in range(len(data)):
        if data[i] == 13: #'\r'
            data[i] = 10 # \n
    with open(out_filename, mode="wb") as f:
        f.write(data)


def prepare_challenge_data(data_path, challenge_data_path, intermediate_data_path, 
    f_root, f_listmode, f_mumap, f_attn, f_norm, f_stir_norm, f_template,
    f_prompts, f_multfactors, f_additive, f_randoms, f_af, f_acf, f_scatter, start, stop):

    f_listmode = os.path.join(data_path, f_root + f_listmode)
    f_siemens_attn_image = os.path.join(data_path, f_root + f_mumap)
    f_siemens_attn_header = f_siemens_attn_image + '.hdr'
    f_siemens_norm = os.path.join(data_path, f_root + f_norm)
    f_siemens_norm_header = f_siemens_norm + '.hdr'
    f_stir_norm_header = os.path.join(challenge_data_path, f_stir_norm)
    f_stir_attn_header = os.path.join(challenge_data_path, f_root + f_attn)
    #f_template = os.path.join(sirf_data_path, f_templ)
    f_prompts = os.path.join(challenge_data_path, f_prompts)
    f_multfactors = os.path.join(challenge_data_path, f_multfactors)
    f_additive = os.path.join(challenge_data_path, f_additive)
    f_randoms = os.path.join(intermediate_data_path, f_randoms)
    f_af = os.path.join(intermediate_data_path, f_af)
    f_acf = os.path.join(intermediate_data_path, f_acf)
    f_scatter = os.path.join(intermediate_data_path, f_scatter)

    os.system('cp ' + f_siemens_attn_image + ' ' + challenge_data_path)
    os.system('convertSiemensInterfileToSTIR.sh ' + f_siemens_attn_header + ' ' + f_stir_attn_header)
    os.system('cp ' + f_siemens_norm + ' ' + challenge_data_path)

    fix_siemens_norm_EOL(f_siemens_norm_header, f_stir_norm_header)

    # engine's messages go to files, except error messages, which go to stdout
    _ = pet.MessageRedirector('info.txt', 'warn.txt')

    # select acquisition data storage scheme
    pet.AcquisitionData.set_storage_scheme('memory')

    # read acquisition data template
    acq_data_template = pet.AcquisitionData(f_template)
    logger.info(acq_data_template.norm())

    output_prefix = "prompts"

    listmode_data = pet.ListmodeData(f_listmode)

    logger.info("Processing listmode data...")
    logger.info(f"Start time: {start} sec. End time: {stop} sec.")
    logger.info(f"Output prefix: {output_prefix}")
    # create listmode-to-sinograms converter object
    lm2sino = pet.ListmodeToSinograms()
    lm2sino.set_input(listmode_data)
    lm2sino.set_output_prefix(output_prefix)
    lm2sino.set_template(acq_data_template)
    lm2sino.set_time_interval(start, stop)
    lm2sino.set_up()
    lm2sino.process()

    prompts = lm2sino.get_output()
    randoms = lm2sino.estimate_randoms()
    logger.info('data shape: %s' % repr(prompts.shape))
    logger.info('prompts norm: %f' % prompts.norm())
    logger.info('randoms norm: %f' % randoms.norm())
    
    logger.info(f'writing prompts to {f_prompts} and randoms to {f_randoms}')
    prompts.write(f_prompts)
    randoms.write(f_randoms)

    attn_image = pet.ImageData(f_stir_attn_header)
    af, acf = pet.AcquisitionSensitivityModel.compute_attenuation_factors(prompts, attn_image)
    logger.info('norm of the attenuation factor: %f' % af.norm())
    logger.info('norm of the attenuation correction factor: %f' % acf.norm())
    logger.info(f'writing intermediate attenuation factors to {f_af}')
    logger.info(f'writing intermediate attenuation coefficient factors to {f_acf}')
    af.write(f_af)
    acf.write(f_acf)

    asm = pet.AcquisitionSensitivityModel(f_stir_norm_header)
    se = pet.ScatterEstimator()
    se.set_input(prompts)
    se.set_attenuation_image(attn_image)
    se.set_randoms(randoms)
    se.set_asm(asm)
    se.set_attenuation_correction_factors(acf)
    se.set_num_iterations(4)
    se.set_OSEM_num_subsets(7)
    se.set_output_prefix(f_scatter)
    se.set_up()
    se.process()
    scatter = se.get_output()
    logger.info('norm of the scatter estimate: %f' % scatter.norm())

    multfact = af.clone()
    asm.set_up(af)
    asm.unnormalise(multfact)
    logger.info(multfact.norm())
    logger.info(f'writing multiplicative factors to {f_multfactors}')
    multfact.write(f_multfactors)

    background = randoms + scatter
    logger.info('norm of the backgrount term: %f' % background.norm())

    asm_mf = pet.AcquisitionSensitivityModel(multfact)
    asm_mf.set_up(background)
    asm_mf.normalise(background)
    logger.info('norm of the additive term: %f' % background.norm())
    logger.info(f'writing additive term to {f_additive}')
    
    background.write(f_additive)

    return

