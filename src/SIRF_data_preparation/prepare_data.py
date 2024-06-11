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

    logging.debug(f"Start time for data: {args.start} sec")
    logging.debug(f"End time for data: {args.end} sec")

    start = args.start
    end = args.end
    logging.info(f"Start time for data: {start} sec")
    logging.info(f"End time for data: {end} sec")
    
    if args.raw_data_path is None:
        data_path = exercises_data_path('PET', 'mMR', 'NEMA_IQ')
    else:
        data_path = args.raw_data_path
    
    data_path = os.path.abspath(data_path)
    logging.debug(f"Raw data path: {data_path}")


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

