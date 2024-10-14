# Copyright 2024 University College London
# Licence: Apache-2.0

# %% imports
import typing
import sirf.Reg as Reg
import sirf.STIR as STIR
import os

# %%
__version__ = "0.1.0"

# %% Functions to convert between STIR and Reg.ImageData (via writing to file)
# converters directly via the objects are not all implemented, and we want them on file anyway
# WARNING: There will be flips in nii_to_STIR if the STIR.ImageData contains PatientPosition
# information AND it is not in HFS. This is because .nii cannot store this information
# and STIR reads .nii as HFS.
# WARNING: filename_prefix etc should not contain dots (.)
def nii_to_STIR(image_nii: Reg.ImageData, filename_prefix: str) -> STIR.ImageData:
    """Write Reg.ImageData as nii, read as STIR.ImageData and write that as well"""
    image_nii.write(filename_prefix + ".nii")
    image = STIR.ImageData(filename_prefix + ".nii")
    image.write(filename_prefix + ".hv")
    return image


def STIR_to_nii(image: STIR.ImageData, filename_nii: str, filename_hv: str | None = None) -> Reg.ImageData:
    """Write STIR.ImageData object as Nifti and read as Reg.ImageData"""
    image.write_par(
        filename_nii,
        os.path.join(
            STIR.get_STIR_examples_dir(),
            "samples",
            "stir_math_ITK_output_file_format.par",
        ),
    )
    nii_image = Reg.ImageData(filename_nii)
    if filename_hv is not None:
        image.write(filename_hv)
    return nii_image


def STIR_to_nii_hv(image: STIR.ImageData, filename_prefix: str) -> Reg.ImageData:
    """Call STIR_to_nii by appendix .nii and .hv"""
    return STIR_to_nii(image, filename_prefix + ".nii", filename_prefix + ".hv")


# %% Function to do rigid registration and return resampler
def register_it(reference_image: Reg.ImageData,
                floating_image: Reg.ImageData) -> typing.Tuple[Reg.ImageData, Reg.NiftyResampler, Reg.NiftyAladinSym]:
    """
    Use rigid registration of floating to reference image
    Return both the registered image and the resampler.
    Currently the resampler is set to use NN interpolation (such that it can be used for VOIs)
    Note that `registered = resampler.forward(floating_image)` up to interpolation choices
    """
    reg = Reg.NiftyAladinSym()
    reg.set_parameter("SetPerformRigid", "1")
    reg.set_parameter("SetPerformAffine", "0")
    reg.set_reference_image(reference_image)
    reg.add_floating_image(floating_image)
    reg.process()
    resampler = Reg.NiftyResampler()
    resampler.add_transformation(reg.get_deformation_field_forward())
    resampler.set_interpolation_type_to_nearest_neighbour()
    resampler.set_reference_image(reference_image)
    resampler.set_floating_image(floating_image)
    return (reg.get_output(0), resampler, reg)


# %% resample Reg.ImageData and write to file
def resample_STIR(resampler: Reg.NiftyResampler, image_nii: Reg.ImageData, filename_prefix: str) -> STIR.ImageData:
    res_nii = resampler.forward(image_nii)
    return nii_to_STIR(res_nii, filename_prefix)
