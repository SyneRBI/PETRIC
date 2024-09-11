# %%
# """Preliminary file to check evolution of metrics as well as pass_index"""
# %load_ext autoreload
# %autoreload 2
from pathlib import Path

import matplotlib.pyplot as plt
import numpy

import sirf.STIR as STIR
from petric import OUTDIR, SRCDIR, QualityMetrics, get_data
from SIRF_data_preparation import data_QC
from SIRF_data_preparation.dataset_settings import get_settings
from SIRF_data_preparation.evaluation_utilities import get_metrics, pass_index, plot_metrics, read_objectives

if not all((SRCDIR.is_dir(), OUTDIR.is_dir())):
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
    OUTDIR = PETRICDIR / 'output'
STIR.AcquisitionData.set_storage_scheme('memory')
STIR.set_verbosity(0)

# scanID = 'Siemens_Vision600_thorax'
# scanID = 'NeuroLF_Hoffman_Dataset'
# scanID = 'Siemens_mMR_NEMA_IQ'
scanID = 'Mediso_NEMA_IQ'

srcdir = SRCDIR / scanID
outdir = OUTDIR / scanID
OSEMdir = outdir / 'OSEM'
datadir = outdir / 'BSREM'
# we will check for images obtained after restarting BSREM (with new settings)
datadir1 = outdir / 'BSREM_cont'

OSEM_image = STIR.ImageData(str(datadir / 'iter_0000.hv'))

settings = get_settings(scanID)
slices = settings.slices

cmax = OSEM_image.max()

image = data_QC.plot_image_if_exists(str(datadir / 'iter_final'), **slices, vmax=cmax)
# image2=STIR.ImageData(datadir+'iter_14000.hv')
image2 = OSEM_image
diff = image2 - image
print("norm diff:", diff.abs().max() / image.max())
data_QC.plot_image(diff, **slices, vmin=-cmax / 100, vmax=cmax / 100)

objs = read_objectives(datadir)
if datadir1.is_dir():
    objs0 = objs.copy()
    objs1 = read_objectives(datadir1)
    tmp = objs1.copy()
    tmp[:, 0] += objs[-1, 0]
    objs = numpy.concatenate((objs, tmp))
fig = plt.figure()
plt.plot(objs[2:, 0], objs[2:, 1])
# %%
fig.savefig(outdir / f'{scanID}_BSREM_objectives.png')
# %%
fig = plt.figure()
plt.plot(objs[50:, 0], objs[50:, 1])
# %%
fig.savefig(outdir / f'{scanID}_BSREM_objectives_last.png')

# %%
data = get_data(srcdir=srcdir, outdir=outdir / 'test')
if datadir1.is_dir():
    reference_image = STIR.ImageData(str(datadir1 / 'iter_final.hv'))
else:
    reference_image = STIR.ImageData(str(datadir / 'iter_final.hv'))
qm = QualityMetrics(reference_image, data.whole_object_mask, data.background_mask, tb_summary_writer=None,
                    voi_mask_dict=data.voi_masks)
# %% get update ("iteration") numbers from objective functions
last_iteration = int(objs[-1, 0] + .5)
# find interval(don't use last value, as that interval can be smaller)
iteration_interval = int(objs[-2, 0] - objs[-3, 0] + .5)
if datadir1.is_dir():
    last_iteration = int(objs0[-1, 0] + .5)
    iteration_interval = int(objs0[-1, 0] - objs0[-2, 0] + .5) * 2
# %%
iters = range(0, last_iteration, iteration_interval)
m = get_metrics(qm, iters, srcdir=datadir)
# %%
OSEMobjs = read_objectives(OSEMdir)
OSEMiters = OSEMobjs[:, 0].astype(int)
OSEMm = get_metrics(qm, OSEMiters, srcdir=OSEMdir)
# %%
fig = plt.figure()
plot_metrics(iters, m, qm.keys(), '_BSREM')
plot_metrics(OSEMiters, OSEMm, qm.keys(), '_OSEM')
[ax.set_xlim(0, 400) for ax in fig.axes]
# %%
fig.savefig(outdir / f'{scanID}_metrics_BSREM_OSEM.png')
# %%
fig = plt.figure()
plot_metrics(iters, m, qm.keys(), '_BSREM')
fig.axes[0].set_ylim(0, .04)
fig.axes[1].set_ylim(0, .02)
fig.savefig(outdir / f'{scanID}_metrics_BSREM.png')
# %%
m1 = None
if datadir1.is_dir():
    last_iteration1 = int(objs1[-1, 0] + .5)
    iteration_interval1 = int(objs1[-1, 0] - objs1[-2, 0] + .5) * 2
    iters1 = range(0, last_iteration1, iteration_interval1)
    m1 = get_metrics(qm, iters1, srcdir=datadir1)
# %%
if m1 is not None:
    fig = plt.figure()
    plot_metrics(objs0[-1, 0] + iters1, m1, qm.keys(), '_BSREM_cont')
    fig.savefig(outdir / f'{scanID}_metrics_BSREM.png')

# %%
idx = pass_index(m, numpy.array([.01, .01] + [.005 for i in range(len(data.voi_masks))]), 10)
iter = iters[idx]
print(iter)
image = STIR.ImageData(str(datadir / f"iter_{iter:04d}.hv"))
plt.figure()
data_QC.plot_image(image, **slices, vmax=cmax)
plt.savefig(outdir / f'{scanID}_image_at_0.01_0.005.png')

plt.figure()
data_QC.plot_image(image - data.OSEM_image, **slices, vmin=-cmax / 20, vmax=cmax / 20)
plt.savefig(outdir / f'{scanID}_OSEM_diff_image_at_0.01_0.005.png')
plt.figure()
data_QC.plot_image(image - reference_image, **slices, vmin=-cmax / 100, vmax=cmax / 100)
plt.savefig(outdir / f'{scanID}_ref_diff_image_at_0.01_0.005.png')
