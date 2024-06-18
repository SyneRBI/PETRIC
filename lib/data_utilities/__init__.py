'''Library of Siemens data preparation utilities.'''

# Author: Ashley Gillman, Kris Thielemans, Evgueni Ovtchinnikov
# Copyright (C) 2021 Commonwealth Scientific and Industrial Research Organisation
# Copyright (C) 2024 University College London
# Copyright (C) 2024 STFC, UK Research and Innovation
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

logger = logging.getLogger("PETRIC")


def the_data_path(*data_type):
    '''
    Returns the path to data.

    data_type: either 'PET', 'MR' or 'Synergistic', or use multiple arguments for
    subdirectories like the_data_path('PET', 'mMR', 'NEMA_IQ').
    '''
    try:
        from .data_path import data_path
    except ImportError:
        raise RuntimeError(
            "Path to data not found.")

    return os.path.join(data_path, *data_type)


def fix_siemens_norm_EOL(in_filename, out_filename):
    with open(in_filename, mode="rb") as f:
        data = bytearray(f.read())
    for i in range(len(data)):
        if data[i] == 13: #'\r'
            data[i] = 10 # \n
    with open(out_filename, mode="wb") as f:
        f.write(data)


def prepare_challenge_Siemens_data(data_path, challenge_data_path, intermediate_data_path,
    f_root, f_listmode, f_mumap, f_attn, f_norm, f_stir_norm, f_template,
    f_prompts, f_multfactors, f_additive, f_randoms, f_af, f_acf, f_scatter, start, stop):
    '''Prepares data for SyneRBI Challenge24

    data_path: path to Siemens data
    challenge_data_path: path to prepared data
    data_path: path to intermediate data
    f_root: common prefix for some data files' names (list-mode data, mu-maps etc.)
    f_listmode: list-mode data file suffix
    f_numap: mu-map file suffix
    f_attn: mu-map header suffix
    f_norm: Siemens normalisation data file suffix
    f_stir_norm: STIR normalisation data file name
    f_template: template for prompts file name
    f_prompts: prompts file name
    f_multfactors: multfactors file name
    f_additive: additive term file name
    f_randoms: estimated randoms file name
    f_af: attenuation factor file name
    f_acf: attenuation correction factor file name
    f_scatter: scatter estimate file name
    start: start time for data acquisition
    stop: end time for data acquisition
    '''

    logging.info(f"Start time for data: {start} sec")
    logging.info(f"End time for data: {stop} sec")

    f_listmode = os.path.join(data_path, f_root + f_listmode)
    f_siemens_attn_image = os.path.join(data_path, f_root + f_mumap)
    f_siemens_attn_header = f_siemens_attn_image + '.hdr'
    f_siemens_norm = os.path.join(data_path, f_root + f_norm)
    f_siemens_norm_header = f_siemens_norm + '.hdr'
    f_stir_norm_header = os.path.join(challenge_data_path, f_stir_norm)
    f_stir_attn_header = os.path.join(challenge_data_path, f_root + f_attn)
    f_prompts = os.path.join(challenge_data_path, f_prompts)
    f_multfactors = os.path.join(challenge_data_path, f_multfactors)
    f_additive = os.path.join(challenge_data_path, f_additive)
    f_randoms = os.path.join(intermediate_data_path, f_randoms)
    f_af = os.path.join(intermediate_data_path, f_af)
    f_acf = os.path.join(intermediate_data_path, f_acf)
    f_scatter = os.path.join(intermediate_data_path, f_scatter)
    f_info = os.path.join(intermediate_data_path, 'info.txt')
    f_warn = os.path.join(intermediate_data_path, 'warn.txt')

    os.system('cp ' + f_siemens_attn_image + ' ' + challenge_data_path)
    os.system('convertSiemensInterfileToSTIR.sh ' + f_siemens_attn_header + ' ' + f_stir_attn_header)
    os.system('cp ' + f_siemens_norm + ' ' + challenge_data_path)

    fix_siemens_norm_EOL(f_siemens_norm_header, f_stir_norm_header)

    # engine's messages go to files, except error messages, which go to stdout
    _ = pet.MessageRedirector(f_info, f_warn)

    # select acquisition data storage scheme
    pet.AcquisitionData.set_storage_scheme('memory')

    # read acquisition data template
    acq_data_template = pet.AcquisitionData(f_template)
    logger.info(acq_data_template.norm())

    output_prefix = os.path.join(challenge_data_path, "prompts")

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
    logger.info('norm of the background term: %f' % background.norm())

    asm_mf = pet.AcquisitionSensitivityModel(multfact)
    asm_mf.set_up(background)
    asm_mf.normalise(background)
    logger.info('norm of the additive term: %f' % background.norm())
    logger.info(f'writing additive term to {f_additive}')
    
    background.write(f_additive)

    return

