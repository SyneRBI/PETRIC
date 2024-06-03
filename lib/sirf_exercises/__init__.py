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


def exercises_data_path(*data_type):
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


def cd_to_working_dir(*subfolders):
    '''
    Creates and changes the current directory to a working directory for the
    current exercise, based on the argument(s). If multiple
    strings are given, they will be treated as subdirectories.

    Implementation detail: this is defined as
    {exercises_data_path()}/working_folder/{subfolders[0]}/{subfolders[1]}/...

    subfolders: the path will include this.
    Multiple arguments can be given for nested subdirectories.
    '''
    try:
        from .working_path import working_dir
        working_dir = os.path.join(working_dir, *subfolders)
    except ImportError:
        working_dir = exercises_data_path('working_folder', *subfolders)
    os.makedirs(working_dir, exist_ok=True)
    os.chdir(working_dir)


def fix_siemens_norm_EOL(in_filename, out_filename):
    with open(in_filename, mode="rb") as f:
        data = bytearray(f.read())
    for i in range(len(data)):
        if data[i] == 13: #'\r'
            data[i] = 10 # \n
    with open(out_filename, mode="wb") as f:
        f.write(data)


def prepare_challenge_data(data_path, sirf_data_path, challenge_data_path, intermediate_data_path, 
    f_root, f_listmode, f_mumap, f_attn, f_norm, f_stir_norm, f_templ,
    f_prompts, f_multfactors, f_additive, f_randoms, f_af, f_acf, f_scatter):

    f_listmode = os.path.join(data_path, f_root + f_listmode)
    f_siemens_attn_image = os.path.join(data_path, f_root + f_mumap)
    f_siemens_attn_header = f_siemens_attn_image + '.hdr'
    f_siemens_norm = os.path.join(data_path, f_root + f_norm)
    f_siemens_norm_header = f_siemens_norm + '.hdr'
    f_stir_norm_header = os.path.join(challenge_data_path, f_stir_norm)
    f_stir_attn_header = os.path.join(challenge_data_path, f_root + f_attn)
    f_template = os.path.join(sirf_data_path, f_templ)
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
    print(acq_data_template.norm())

    listmode_data = pet.ListmodeData(f_listmode)

    # create listmode-to-sinograms converter object
    lm2sino = pet.ListmodeToSinograms()

    prompts, randoms = lm2sino.prompts_and_randoms_from_listmode(listmode_data, 0, 10, acq_data_template)
    print('data shape: %s' % repr(prompts.shape))
    print('prompts norm: %f' % prompts.norm())
    print('randoms norm: %f' % randoms.norm())
    prompts.write(f_prompts)
    randoms.write(f_randoms)

    attn_image = pet.ImageData(f_stir_attn_header)
    af, acf = pet.AcquisitionSensitivityModel.compute_attenuation_factors(prompts, attn_image)
    print('norm of the attenuation factor: %f' % af.norm())
    print('norm of the attenuation correction factor: %f' % acf.norm())
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
    print('norm of the scatter estimate: %f' % scatter.norm())

    multfact = af.clone()
    asm.set_up(af)
    asm.unnormalise(multfact)
    print(multfact.norm())
    multfact.write(f_multfactors)

    background = randoms + scatter
    print('norm of the backgrount term: %f' % background.norm())

    asm_mf = pet.AcquisitionSensitivityModel(multfact)
    asm_mf.set_up(background)
    asm_mf.normalise(background)
    print('norm of the additive term: %f' % background.norm())
    background.write(f_additive)

    return

