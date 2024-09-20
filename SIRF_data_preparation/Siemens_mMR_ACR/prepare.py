import argparse
import logging
import os

from ..data_utilities import prepare_challenge_Siemens_data, the_data_path, the_orgdata_path

scanID = 'Siemens_mMR_ACR'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SyneRBI PETRIC Siemens mMR ACR data preparation script.')

    parser.add_argument('--log', type=str, default='warning')
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=500)
    parser.add_argument('--raw_data_path', type=str, default=None)
    args = parser.parse_args()

    if args.log in ['debug', 'info', 'warning', 'error', 'critical']:
        level = eval(f'logging.{args.log.upper()}')
        logging.basicConfig(level=level)
        logging.info(f"Setting logging level to {args.log.upper()}")

    start = args.start
    end = args.end

    if args.raw_data_path is None:
        data_path = the_orgdata_path(scanID, 'processing')
    else:
        data_path = args.raw_data_path

    data_path = os.path.abspath(data_path)
    logging.debug(f"Raw data path: {data_path}")

    intermediate_data_path = the_orgdata_path(scanID, 'processing')
    output_path = the_data_path(scanID)

    os.makedirs(output_path, exist_ok=True)
    os.chdir(output_path)
    os.makedirs(intermediate_data_path, exist_ok=True)

    f_template = os.path.join(data_path, 'mMR_template_span11.hs')

    prepare_challenge_Siemens_data(data_path, output_path, intermediate_data_path, '', 'list.l.hdr', 'reg_mumap.v',
                                   'reg_mumap.hv', 'norm.n', 'norm.n.hdr', f_template, 'prompts', 'mult_factors',
                                   'additive_term', 'randoms', 'attenuation_factor', 'attenuation_correction_factor',
                                   'scatter', start, end)
