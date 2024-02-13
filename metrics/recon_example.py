#%%
from cil.utilities import dataexample
from cil.utilities.display import show2D
from cil.recon import FDK
from cil.processors import TransmissionAbsorptionConverter, Slicer

ground_truth = dataexample.SIMULATED_SPHERE_VOLUME.get()

data = dataexample.SIMULATED_CONE_BEAM_DATA.get()
twoD = True
if twoD:
    data = data.get_slice(vertical='centre')
    ground_truth = ground_truth.get_slice(vertical='centre')

absorption = TransmissionAbsorptionConverter()(data)
absorption = Slicer(roi={'angle':(0, -1, 5)})(absorption)

ig = ground_truth.geometry

#%%
recon = FDK(absorption, image_geometry=ig).run()
#%%
show2D([ground_truth, recon], title = ['Ground Truth', 'FDK Reconstruction'], origin = 'upper', num_cols = 2)

# %%
from cil.plugins.tigre import ProjectionOperator
from cil.optimisation.algorithms import FISTA 
from cil.optimisation.functions import LeastSquares, IndicatorBox, ZeroFunction, TotalVariation
from cil.optimisation.operators import GradientOperator
from cil.optimisation.utilities import callbacks

#%%
A = ProjectionOperator(image_geometry=ig, 
                       acquisition_geometry=absorption.geometry)

F = LeastSquares(A = A, b = absorption)
G = IndicatorBox(lower=0)

grad = GradientOperator(domain_geometry=ig)
#%%
alpha = 0.1 * A.norm()/grad.norm()
G = alpha * TotalVariation(max_iteration=2)

algo = FISTA(initial = ig.allocate(), f = F, g = G)

#%%
# Image metrics callback
import img_quality_cil_stir as imgq
import tensorboardX
from datetime import datetime
import numpy as np
# create a tensorboardX summary writer
dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
tb_summary_writer = tensorboardX.SummaryWriter(f'recons/exp-{dt_string}')

#%% create masks
top = ig.allocate(0)
bottom = ig.allocate(0)

top.fill(
    np.asarray(ground_truth.array > 0.8 * ground_truth.max(), 
               dtype=np.float32)
    )
bottom.fill(
    np.asarray(np.invert(ground_truth.array < 0.4 * ground_truth.max()), 
               dtype=np.float32)
)
#%%
show2D([ground_truth, top, bottom], num_cols=3)
#%%
# setup a 2 binary ROI images
roi_image_dict = {
    'top' : top,
    'bottom' : bottom
}


def MSE(x,y):
    """ mean squared error between two numpy arrays
    """
    return ((x-y)**2).mean()

def MAE(x,y):
    """ mean absolute error between two numpy arrays
    """
    return np.abs(x-y).mean()

def PSNR(x, y, scale = None):
    """ peak signal to noise ratio between two numpy arrays x and y
        y is considered to be the reference array and the default scale
        needed for the PSNR is assumed to be the max of this array
    """
  
    mse = ((x-y)**2).mean()
  
    if scale == None:
        scale = y.max()
  
    return 10*np.log10((scale**2) / mse)


# instantiate ImageQualityCallback
img_qual_callback = imgq.ImageQualityCallback(ground_truth, tb_summary_writer,
                                              roi_mask_dict = roi_image_dict,
                                              metrics_dict = {'MSE':MSE, 
                                                              'MAE':MAE, 
                                                              'PSNR':PSNR},
                                              statistics_dict = {'MEAN': (lambda x: x.mean()),
                                                                 'STDDEV': (lambda x: x.std()),
                                                                 'MAX': (lambda x: x.max()),
                                                                 'COM': (lambda x: np.array([3,2,1]))},
                                              )
sigmas_mm = [5.0, 8.0]
filters = {}
for sigma in sigmas_mm:
    filters[f"Gaussian_{sigma}"] = imgq.image_quality_callback.GaussianFilter(post_smoothing_fwhm_mm=sigma, voxel_size_mm=img_qual_callback.voxel_size_mm)

img_qual_callback.set_filters(filters)

#%%
algo.run(100, callbacks=[callbacks.ProgressCallback(), 
                        img_qual_callback])
# %%

show2D([ground_truth, algo.solution], title = ['Ground Truth', 'FISTA Reconstruction'], origin = 'upper', num_cols = 2)
# %%
