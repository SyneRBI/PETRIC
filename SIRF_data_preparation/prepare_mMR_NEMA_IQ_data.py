import os
import sys
this_directory = os.path.dirname(__file__)
sys.path.append(this_directory)
repo_directory = os.path.dirname(this_directory)
challenge_data_path = os.path.join(repo_directory, 'data')

import importlib
pet = importlib.import_module('sirf.STIR')

from sirf.Utilities import examples_data_path
from data_utilities import the_data_path
from data_utilities import prepare_challenge_Siemens_data

import logging
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SyneRBI Challenge 2024 data preparation script.')

    parser.add_argument('--log', type=str, default='warning')
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=600)
    parser.add_argument('--raw_data_path', type=str, default=None)
    args = parser.parse_args()

    if args.log in ['debug', 'info', 'warning', 'error', 'critical']:
        level = eval(f'logging.{args.log.upper()}')
        logging.basicConfig(level=level)
        logging.info(f"Setting logging level to {args.log.upper()}")

    start = args.start
    end = args.end

    if args.raw_data_path is None:
        data_path = the_data_path('PET', 'mMR', 'NEMA_IQ')
    else:
        data_path = args.raw_data_path

    data_path = os.path.abspath(data_path)
    logging.debug(f"Raw data path: {data_path}")


    sirf_data_path = os.path.join(examples_data_path('PET'), 'mMR')
    intermediate_data_path = os.path.join(challenge_data_path, 'intermediate')
    os.makedirs(challenge_data_path, exist_ok=True)
    os.chdir(challenge_data_path)
    os.makedirs(intermediate_data_path, exist_ok=True)

    f_template = os.path.join(sirf_data_path, 'mMR_template_span11')
    os.system('cp ' + f_template + '* ' + challenge_data_path)

    prepare_challenge_Siemens_data(data_path, challenge_data_path, intermediate_data_path, '20170809_NEMA_',
        '60min_UCL.l.hdr', 'MUMAP_UCL.v', 'MUMAP_UCL.hv', 'UCL.n', 'norm.n.hdr', f_template + '.hs',
        'prompts', 'multfactors', 'additive_term', 'randoms',
        'attenuation_factor', 'attenuation_correction_factor', 'scatter', start, end)
