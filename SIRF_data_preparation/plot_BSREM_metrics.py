#%%
import os
from pathlib import Path
PETRICDIR=Path(os.path.expanduser('~/devel/PETRIC'))
import sys
sys.path.insert(0, str(PETRICDIR))
#%%
%load_ext autoreload
%autoreload 2
#%%
import csv
import numpy
import matplotlib.pyplot as plt
from pathlib import Path
import sirf.STIR as STIR
import SIRF_data_preparation.data_QC as data_QC
from SIRF_data_preparation.evaluation_utilities import read_objectives, get_metrics, plot_metrics
from petric import QualityMetrics, get_data, SRCDIR
#%%
if not SRCDIR.is_dir():
    SRCDIR = PETRICDIR / 'data'
#%%
STIR.AcquisitionData.set_storage_scheme('memory')
# set-up redirection of STIR messages to files
#_ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
STIR.set_verbosity(0)
# %% read
scanID = 'Siemens_Vision600_thorax'
#scanID = 'NeuroLF_Hoffman_Dataset'
# scanID = 'Siemens_mMR_NEMA_IQ'
srcdir=SRCDIR / scanID
OSEMdir = PETRICDIR /  'output' / ('OSEM_' + scanID)
datadir = PETRICDIR /  'output' / ('BSREM_' + scanID)
datadir1 = PETRICDIR /  'output' / ('BSREM_' + scanID + '_cont')

OSEM_image = STIR.ImageData(str(datadir / 'iter_0000.hv'))
if scanID == 'Siemens_mMR_NEMA_IQ':
    slices = { 'transverse_slice': 72, 'coronal_slice': 109, 'sagittal_slice': 89}
else:
    slices = {}
cmax = OSEM_image.max()

#%% convert old to new
if (datadir /  'obj.csv').is_file() and not (datadir / 'org_objectives.csv').is_file():
    print('converting')
    with open(datadir /  'obj.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        objs = [[float(s) for s in next(reader)], [float(s) for s in next(reader)]]
        objs = numpy.array(objs)
    objs = objs.transpose()
    os.rename(datadir / 'objectives.csv', datadir / 'org_objectives.csv')
    with open(datadir /  'objectives.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['iter', 'objective'])
        writer.writerows(objs)
    
#%%
image=data_QC.plot_image_if_exists(str(datadir /  'iter_final'), **slices, vmax=cmax)
#%%
#image2=STIR.ImageData(datadir+'iter_14000.hv')
image2 = OSEM_image
diff = image2 - image
print(diff.abs().max()/image.max())
data_QC.plot_image(diff,**slices, vmin=-cmax/100, vmax=cmax/100)

#%%
objs = read_objectives(datadir)
if datadir1.is_dir():
    objs0 = objs.copy()
    objs1 = read_objectives(datadir1)
    tmp = objs1.copy()
    tmp[:, 0] += objs[-1, 0]
    objs = numpy.concatenate((objs, tmp))
fig = plt.figure()
plt.plot(objs[2:,0], objs[2:,1])
#%%
fig.savefig(PETRICDIR / 'output' / (scanID + '_BSREM_objectives.png'))
#%%
fig = plt.figure()
plt.plot(objs[50:,0], objs[50:,1])
#%%
fig.savefig(PETRICDIR / 'output' / (scanID + '_BSREM_objectives_last.png'))

#%%
data = get_data(srcdir=srcdir, outdir='output/test')
# %%
qm = QualityMetrics(data.reference_image, data.whole_object_mask, data.background_mask,
            tb_summary_writer=None,
            voi_mask_dict=data.voi_masks)
#%%
last_iteration = int(objs[-1,0]+.5)
iteration_interval = int(objs[-1,0]-objs[-2,0]+.5)
#%%
if datadir1.is_dir():
    last_iteration = int(objs0[-1,0]+.5)
#%%
iters = range(0, last_iteration, iteration_interval)
m = get_metrics(qm, iters, srcdir=datadir)
#%%
OSEMiters = range(0, 400, 20)
OSEMm = get_metrics(qm, OSEMiters, srcdir=OSEMdir)
#%%
fig = plt.figure()
plot_metrics(iters, m, qm.keys(), '_BSREM')
plot_metrics(OSEMiters, OSEMm, qm.keys(), '_OSEM')
[ax.set_xlim(0,400) for ax in fig.axes ]
# %%
fig.savefig(PETRICDIR / 'output' / (scanID + '_metrics_BSREM_OSEM.png'))
#%%
fig = plt.figure()
plot_metrics(iters, m, qm.keys(), '_BSREM')
fig.axes[0].set_ylim(0,.04)
fig.axes[1].set_ylim(0,.02)
fig.savefig(PETRICDIR / 'output' / (scanID + '_metrics_BSREM.png'))
#%%
m1 = None
if datadir1.is_dir():
    last_iteration1 = int(objs1[-1,0]+.5)
    iteration_interval1 = int(objs1[-1,0]-objs1[-2,0]+.5)*2
    iters1 = range(0, last_iteration1, iteration_interval1)
    m1 = get_metrics(qm, iters1, srcdir=datadir1)
#%%
if m1 is not None:
    fig = plt.figure()
    plot_metrics(objs0[-1,0]+iters1, m1, qm.keys(), '_BSREM_cont')
    fig.savefig(PETRICDIR / 'output' / (scanID + '_metrics_BSREM.png'))

