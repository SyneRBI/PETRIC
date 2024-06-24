import numpy
import matplotlib.pyplot as plt
import os
import sys
import sirf.STIR as STIR
from sirf.Utilities import examples_data_path
#from sirf_exercises import exercises_data_path


# Import functionality from the Python files in SIRF-Contribs. (Note that in most set-ups, this will be from the installed files.)

from sirf.contrib.partitioner import partitioner
from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.BSREM.BSREM import BSREM2
# Needed for get_subsets()
STIR.AcquisitionData.set_storage_scheme('memory')
# set-up redirection of STIR messages to files
_ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
# fewer messages from STIR and SIRF (set to higher value to diagnose have problems)
STIR.set_verbosity(0)

#%% definitions

# do not modify this one!
def construct_RDP(penalty_strength, initial_image, kappa, max_scaling=1e-3):
    '''
    Construct a smoothed Relative Difference Prior (RDP)

    `initial_image` is used to determine a smoothing factor (epsilon).
    `kappa` is used to pass voxel-dependent weights.
    '''
    prior = STIR.RelativeDifferencePrior()
    # need to make it differentiable
    epsilon = initial_image.max() * max_scaling
    prior.set_epsilon(epsilon)
    prior.set_penalisation_factor(penalty_strength)
    prior.set_kappa(kappa)
    prior.set_up(initial_image)
    return prior

def add_prior_to_obj_funs(obj_funs, prior, initial_image):
    '''
    Add prior evenly to every objective function in the obj_funs list.

    WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
    WARNING: modifies elements of obj_funs
    '''
    # evenly distribute prior over subsets
    prior.set_penalisation_factor(prior.get_penalisation_factor() / len(obj_funs));
    prior.set_up(initial_image)
    for f in obj_funs:
        f.set_prior(prior)

#%% read
acquired_data = STIR.AcquisitionData('prompts.hs')
additive_term = STIR.AcquisitionData('additive_term.hs')
mult_factors = STIR.AcquisitionData('mult_factors.hs')
OSEM_image = STIR.ImageData('OSEM_image.hv')
kappa = STIR.ImageData('kappa.hv')
penalty_strength = 1/700

prior = construct_RDP(penalty_strength, OSEM_image, kappa)

#%% go

num_subsets = 7
data,acq_models, obj_funs = partitioner.data_partition(acquired_data, additive_term, mult_factors, num_subsets, initial_image=OSEM_image)
add_prior_to_obj_funs(obj_funs, prior, OSEM_image)
bsrem1 = BSREM1(data, obj_funs, initial=OSEM_image, initial_step_size=.3, relaxation_eta=.05, update_objective_interval=10)
bsrem1.run(iterations=80)
bsrem1.x.write('BSREM_80.hv')
im80 = bsrem1.x.clone()
# continue
bsrem1.run(iterations=520)
bsrem1.x.write('BSREM_600.hv')
im600 = bsrem1.x.clone()
bsrem1.run(iterations=60)
bsrem1.x.write('BSREM_660.hv')
im660 = bsrem1.x.clone()

cmax = im80.max()
im_slice = 72
cor_slice = im80.dimensions()[1]//2
plt.figure()
plt.subplot(141)
plt.imshow(im80.as_array()[im_slice,:,:],vmax=cmax)
plt.subplot(142)
plt.imshow(im600.as_array()[im_slice,:,:],vmax=cmax)
plt.subplot(143)
plt.imshow(im660.as_array()[im_slice,:,:],vmax=cmax)
plt.subplot(144)
plt.imshow((im600-im660).as_array()[im_slice,:,:], vmin=-cmax/20, vmax=cmax/20)
plt.savefig('BSREM_transverse_images.png')
plt.figure()
plt.subplot(141)
plt.imshow(im80.as_array()[:,cor_slice,:],vmax=cmax)
plt.subplot(142)
plt.imshow(im600.as_array()[:,cor_slice,:],vmax=cmax)
plt.subplot(143)
plt.imshow(im660.as_array()[:,cor_slice,:],vmax=cmax)
plt.subplot(144)
plt.imshow((im600-im660).as_array()[:,cor_slice,:], vmin=-cmax/20, vmax=cmax/20)
plt.savefig('BSREM_coronal_images.png')
#plt.show()
plt.figure()
plt.plot(bsrem1.iterations, bsrem1.loss)
plt.savefig('BSREM_obj_func.png')
#plt.show()
import csv
with open('BSREM_obj_fun.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    # Write each row of the list to the CSV
    writer.writerows(zip(bsrem1.iterations, bsrem1.loss))
