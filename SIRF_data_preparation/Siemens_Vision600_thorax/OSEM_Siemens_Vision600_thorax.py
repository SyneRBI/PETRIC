#%%
import os
from pathlib import Path
PETRICDIR=Path(os.path.expanduser('~/devel/PETRIC'))
import sys
sys.path.insert(0, str(PETRICDIR))
#%%
from petric import MetricsWithTimeout, get_data, SRCDIR
import main_OSEM
import SIRF_data_preparation.data_QC as data_QC
import matplotlib.pyplot as plt
#%%
outdir="./output/OSEM_Siemens_Vision600_thorax"
data = get_data(srcdir=SRCDIR / 'Siemens_Vision600_thorax',outdir=outdir)
#%%
num_subsets = 5
algo = main_OSEM.Submission(data, num_subsets, update_objective_interval=5)
#%%
algo.run(100, callbacks=[MetricsWithTimeout(seconds=5000, outdir=outdir)])
data_QC.plot_image(algo.get_output())
plt.show()
# %%
algo.run(200, callbacks=[MetricsWithTimeout(seconds=5000, outdir=outdir)])
# %%
