"""Settings for recon and display used in the data preparation"""

from dataclasses import dataclass


@dataclass
class DatasetSettings:
    num_subsets: int
    slices: dict


def get_settings(scanID: str):
    if scanID == 'Siemens_mMR_NEMA_IQ':
        slices = {'transverse_slice': 72, 'coronal_slice': 109} # , 'sagittal_slice': 89}
        num_subsets = 7
    elif scanID == 'NeuroLF_Hoffman_Dataset':
        slices = {'transverse_slice': 72}
        num_subsets = 16
    else:                                                       # Vision
        slices = {}
        num_subsets = 5
    return DatasetSettings(num_subsets, slices)
