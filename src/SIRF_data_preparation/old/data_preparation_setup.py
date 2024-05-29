import os
import sys

import sirf
import sirf.STIR as pet
from sirf.Utilities import show_2D_array
import PET_plot_functions

# Add the SIRF-Exercises Python library to the PYTHONPATH
this_directory = os.path.dirname(__file__)
repo_directory = os.path.dirname(os.path.dirname(this_directory))
sys.path.append(os.path.join(repo_directory, 'lib'))

def fix_siemens_norm_EOL(in_filename, out_filename):
    with open(in_filename, mode="rb") as f:
        data = bytearray(f.read())
    for i in range(len(data)):
        if data[i] == 13: #'\r'
            data[i] = 10 # \n
    with open(out_filename, mode="wb") as f:
        f.write(data)

def sinograms_and_randoms_from_listmode(listmode_filename, duration, template_filename,
                                        sinograms_filename, randoms_filename):

    # select acquisition data storage scheme
    pet.AcquisitionData.set_storage_scheme('memory')

    # read acquisition data template
    acq_data_template = pet.AcquisitionData(template_filename)

    # create listmode-to-sinograms converter object
    lm2sino = pet.ListmodeToSinograms()

    # set input, output and template files
    lm2sino.set_input(listmode_filename)
    lm2sino.set_output_prefix(sinograms_filename)
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
    print('writing sinograms to %s...' % sinograms_filename)
    acq_data.write(sinograms_filename)
    acq_array = acq_data.as_array()
    acq_dim = acq_array.shape
    print('acquisition data dimensions: %dx%dx%dx%d' % acq_dim)
    z = acq_dim[1]//2
    show_2D_array('Acquisition data', acq_array[0,z,:,:])

    del acq_data

    # compute randoms
    print('estimating randoms, please wait...')
    randoms = lm2sino.estimate_randoms()
    print('writing randoms to %s...' % randoms_filename)
    randoms.write(randoms_filename)
    acq_array = randoms.as_array()
    show_2D_array('Randoms', acq_array[0,z,:,:])

def acquisition_sensitivity_from_attenuation(siemens_attn_interfile, template_filename, attn_image_file, ac_sens_filename):

    os.system('convertSiemensInterfileToSTIR.sh ' + siemens_attn_interfile + ' ' + attn_image_file)

    # direct all engine's messages to files
    _ = pet.MessageRedirector('info.txt', 'warn.txt', 'errr.txt')

    # select acquisition data storage scheme
    #pet.AcquisitionData.set_storage_scheme(storage)

    # obtain an acquisition data template
    template = pet.AcquisitionData(template_filename)

    # create uniform acquisition data from template
    print('creating uniform acquisition data...')
    acq_data = pet.AcquisitionData(template)
    acq_data.fill(1.0)

    # read attenuation image
    attn_image = pet.ImageData(attn_image_file)

    # create acquisition model
    am = pet.AcquisitionModelUsingRayTracingMatrix()
    am.set_up(template, attn_image)

    # create acquisition sensitivity model from attenuation image
    print('creating acquisition sensitivity model...')
    asm = pet.AcquisitionSensitivityModel(attn_image, am)
    asm.set_up(template)
##    print('projecting (please wait, may take a while)...')
##    simulated_data = am.forward(attn_image)

    # apply attenuation to the uniform acquisition data to obtain
    # 'bin efficiencies'
    print('applying attenuation (please wait, may take a while)...')
    asm.unnormalise(acq_data)

    acq_data.write(ac_sens_filename)

    # show 'AC factors'
    acq_array = acq_data.as_array()
    acq_dim = acq_array.shape
    z = acq_dim[1]//2
    show_2D_array('Attenuation factors', acq_array[0,z,:,:])

    return acq_data

def estimate_scatter(raw_data_file, randoms_data_file, norm_file, mu_map_file, ac_factors, scatter_file, interactive = True):
    # Create the Scatter Estimator
    # We can use a STIR parameter file like this
    # par_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parameter_files')
    # se = pet.ScatterEstimator(pet.existing_filepath(par_file_path, 'scatter_estimation.par'))
    # However, we will just use all defaults here, and set variables below.
    se = pet.ScatterEstimator()

    prompts = pet.AcquisitionData(raw_data_file)
    se.set_input(prompts)
    se.set_attenuation_image(pet.ImageData(mu_map_file))
    if randoms_data_file is None:
        randoms = None
    else:
        randoms = pet.AcquisitionData(randoms_data_file)
        se.set_randoms(randoms)
    if not(norm_file is None):
        se.set_asm(pet.AcquisitionSensitivityModel(norm_file))

    if isinstance(ac_factors, str):
        ac_factors = pet.AcquisitionData(ac_factors)
    # invert attenuation factors to get the correction factors,
    # as this is unfortunately what a ScatterEstimator needs
    acf_factors=ac_factors.get_uniform_copy()
    acf_factors.fill(1/ac_factors.as_array())
    del ac_factors

    se.set_attenuation_correction_factors(acf_factors)
    # Could set number of iterations if you want to (we recommend at least 3)
    se.set_num_iterations(4)
    print("number of scatter iterations that will be used: %d" % se.get_num_iterations())
    # Could set number of subsets used by the OSEM reconstruction inside the scatter estimation loop.
    # Here we will set it to 7 (which is in fact the default), which is appropriate for the mMR
    output_prefix = scatter_file
    se.set_OSEM_num_subsets(7)
    se.set_output_prefix(output_prefix)
    se.set_up()
    se.process()
    scatter_estimate = se.get_output()
    scatter_estimate.write(scatter_file + '.hs')
    if not interactive:
        return

    ## show estimated scatter data
    scatter_estimate_as_array = scatter_estimate.as_array()
    show_2D_array('Scatter estimate', scatter_estimate_as_array[0, 0, :, :])

    ## let's draw some profiles to check
    # we will average over all sinograms to reduce noise
    PET_plot_functions.plot_sinogram_profile(prompts, randoms=randoms, scatter=scatter_estimate)

def create_multfactors(norm_file, ac_sens, mult_factors_filename):
    asm_norm = pet.AcquisitionSensitivityModel(norm_file)
    asm_norm.set_up(ac_sens)
    mult_factors = ac_sens.clone()
    asm_norm.unnormalise(mult_factors)
    mult_factors.write(mult_factors_filename)

    # show 
    acq_array = mult_factors.as_array()
    acq_dim = acq_array.shape
    z = acq_dim[1]//2
    show_2D_array('mult factors', acq_array[0,z,:,:])

    return mult_factors

def create_background_and_additive(randoms, scatter, mult_factors, background_filename, additive_term_filename):
    if isinstance(randoms, str):
        randoms = pet.AcquisitionData(randoms)
    if isinstance(scatter, str):
        scatter = pet.AcquisitionData(scatter)
    if isinstance(mult_factors, str):
        mult_factors = pet.AcquisitionData(mult_factors)

    background = randoms + scatter
    background.write(background_filename)

    asm = pet.AcquisitionSensitivityModel(mult_factors)
    asm.set_up(background)
    asm.normalise(background)
    background.write(additive_term_filename)

