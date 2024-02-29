import os
import sys

import sirf
import sirf.STIR as pet
from sirf.Utilities import show_2D_array

# Add the SIRF-Exercises Python library to the PYTHONPATH
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(os.path.dirname(this_directory))
sys.path.append(os.path.join(repo_directory, 'lib'))

def sinograms_and_randoms_from_listmode(listmode_filename, duration, template_filename, \
output_path, sinograms_filename, randoms_filename):

    sino_file = os.path.join(output_path, sinograms_filename)
    rand_file = os.path.join(output_path, randoms_filename)

    # select acquisition data storage scheme
    pet.AcquisitionData.set_storage_scheme('memory')

    # read acquisition data template
    acq_data_template = pet.AcquisitionData(template_filename)

    # create listmode-to-sinograms converter object
    lm2sino = pet.ListmodeToSinograms()

    # set input, output and template files
    lm2sino.set_input(listmode_filename)
    lm2sino.set_output_prefix(sino_file)
    lm2sino.set_template(acq_data_template)

    # set interval
    lm2sino.set_time_interval(duration[0], duration[1])

    # set some flags as examples (the following values are the defaults)
    lm2sino.flag_on('store_prompts')
    lm2sino.flag_off('interactive')

    # set up the converter
    lm2sino.set_up()

    # convert
    lm2sino.process()

    # get access to the sinograms
    acq_data = lm2sino.get_output()
    acq_array = acq_data.as_array()
    acq_dim = acq_array.shape
    print('acquisition data dimensions: %dx%dx%dx%d' % acq_dim)
    z = acq_dim[1]//2
    show_2D_array('Acquisition data', acq_array[0,z,:,:])
    print('writing sinograms to %s...' % sino_file)
    acq_data.write(sino_file)

    # compute randoms
    print('estimating randoms, please wait...')
    randoms = lm2sino.estimate_randoms()
    rnd_array = randoms.as_array()
    show_2D_array('Randoms', rnd_array[0,z,:,:])
    print('writing randoms to %s...' % rand_file)
    randoms.write(rand_file)
