# %%
# %load_ext autoreload
# %%
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy
from data_QC import VOI_mean, plot_image
from scipy import ndimage
from scipy.ndimage import binary_erosion

import sirf.STIR as STIR
from petric import SRCDIR
from SIRF_data_preparation import data_QC

# %%
# %autoreload 2

# %%
# %matplotlib ipympl
# %%
STIR.AcquisitionData.set_storage_scheme('memory')
# set-up redirection of STIR messages to files
# _ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
# fewer messages from STIR and SIRF (set to higher value to diagnose have problems)
STIR.set_verbosity(0)

# %% read
if not SRCDIR.is_dir():
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
datadir = str(SRCDIR / 'Siemens_mMR_NEMA_IQ/')
# %%
OSEM_image = STIR.ImageData(datadir + 'OSEM_image.hv')
im_slice = 72
cor_slice = 109
sag_slice = OSEM_image.dimensions()[2] // 2
cmax = OSEM_image.max()
# %%
slices = {'transverse_slice': 72, 'coronal_slice': 109}
# %% read in original VOIs
orgVOIs = []
for i in range(1, 8):
    orgVOIs.append(STIR.ImageData(datadir + f"S{i}.hv"))
    data_QC.plot_image(orgVOIs[i - 1], **slices)
# %%
reference_image = STIR.ImageData(datadir + 'PETRIC/reference_image.hv')
data_QC.plot_image(reference_image, **slices)
# %% create PETRIC VOIs
whole_object_mask = reference_image.clone()
whole_object_mask.fill(binary_erosion(reference_image.as_array() > reference_image.max() * .05, iterations=2))
data_QC.plot_image(whole_object_mask, **slices)
# %%
background_mask = orgVOIs[6]
VOI1_mask = orgVOIs[4]
VOI2_mask = orgVOIs[2]
VOI3_mask = orgVOIs[0]
# %% write PETRIC VOIs
whole_object_mask.write(datadir + 'PETRIC/VOI_whole_object.hv')
background_mask.write(datadir + 'PETRIC/VOI_background.hv')
VOI1_mask.write(datadir + 'PETRIC/VOI_sphere5.hv')
VOI2_mask.write(datadir + 'PETRIC/VOI_sphere3.hv')
VOI3_mask.write(datadir + 'PETRIC/VOI_sphere1.hv')
# %%
VOIs = (whole_object_mask, background_mask, VOI1_mask, VOI2_mask, VOI3_mask)
# %%
[data_QC.plot_image(VOI, **slices) for VOI in VOIs]
# %%
allVOIs = whole_object_mask.clone() * .2
allVOIs += background_mask
for VOI in VOIs:
    allVOIs += VOI
allVOIs /= allVOIs.max()
# %%
plt.figure()
data_QC.plot_image(reference_image, **slices)
plt.figure()
data_QC.plot_image(reference_image, **slices, alpha=allVOIs)
# %%


def VOI_checks(allVOInames, OSEM_image=None, reference_image=None, srcdir='.', **kwargs):
    if len(allVOInames) == 0:
        return
    OSEM_VOI_values = []
    ref_VOI_values = []
    allVOIs = None
    VOIkwargs = kwargs.copy()
    VOIkwargs['vmax'] = 1
    VOIkwargs['vmin'] = 0
    for VOIname in allVOInames:
        filename = os.path.join(srcdir, VOIname + '.hv')
        if not os.path.isfile(filename):
            print(f"VOI {VOIname} does not exist")
            continue
        VOI = STIR.ImageData(filename)
        COM = numpy.rint(ndimage.measurements.center_of_mass(VOI.as_array()))
        print(COM)
        plt.figure()
        plot_image(VOI, vmin=0, vmax=1, transverse_slice=int(COM[0]), coronal_slice=int(COM[1]),
                   sagittal_slice=int(COM[2]))

        # construct transparency image
        if VOIname == 'VOI_whole_object':
            VOI /= 2
        if allVOIs is None:
            allVOIs = VOI.clone()
        else:
            allVOIs += VOI
        if OSEM_image is not None:
            OSEM_VOI_values.append(VOI_mean(OSEM_image, VOI))
        if reference_image:
            ref_VOI_values.append(VOI_mean(reference_image, VOI))
    allVOIs /= allVOIs.max()

    if OSEM_image is not None:
        plt.figure()
        plot_image(OSEM_image, **kwargs)
        plt.figure()
        plot_image(OSEM_image, alpha=allVOIs, **kwargs)


# %%
VOI_checks(['VOI_whole_object', 'VOI_sphere5'], OSEM_image, srcdir=os.path.join(datadir, 'PETRIC'), **slices)
# %%
OSEM_image
# %%
[data_QC.VOI_mean(OSEM_image, VOI) for VOI in VOIs]
# %%
[data_QC.VOI_mean(reference_image, VOI) for VOI in VOIs]
# %%
data_QC.main(['--srcdir', datadir])
# %%
