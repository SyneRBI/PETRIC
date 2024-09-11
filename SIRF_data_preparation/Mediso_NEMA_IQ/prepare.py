# Set NaNs to zero in additive_term
import numpy as np

import sirf.STIR

additive = sirf.STIR.AcquisitionData('additive_term.hs')
add_arr = additive.as_array()
add_arr = np.nan_to_num(add_arr)
new_add = additive.clone()
new_add.fill(add_arr)
new_add.write('additive_term.hs')
