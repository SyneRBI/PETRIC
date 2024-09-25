"""Settings for recon and display used in the data preparation"""
from dataclasses import dataclass

from petric import DATA_SLICES

DATA_SUBSETS = {
    'Siemens_mMR_NEMA_IQ': 7, 'Siemens_mMR_NEMA_IQ_lowcounts': 7, 'Siemens_mMR_ACR': 7, 'NeuroLF_Hoffman_Dataset': 16,
    'Mediso_NEMA_IQ': 12, 'Siemens_Vision600_thorax': 5, 'GE_DMI3_Torso': 8}


@dataclass
class DatasetSettings:
    num_subsets: int
    slices: dict


def get_settings(scanID: str):
    return DatasetSettings(DATA_SUBSETS[scanID], DATA_SLICES[scanID])
