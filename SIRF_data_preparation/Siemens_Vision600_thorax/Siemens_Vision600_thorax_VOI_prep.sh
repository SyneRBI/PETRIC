#! /bin/bash
# get rid of offset in niftis, as they are currently not in the reconstructed images
for f in *nii.gz; do
   base=${f%%.nii.gz}
   stir_math $base.hv $base.nii.gz
   sed -i -e '/first pixel offset/ d' \
     -e '/!INTERFILE/a !imaging modality := PT' \
    $base.hv
    # patient position is currently not in reconstructed images
    # -e '/type of data/a patient orientation := feet_in' \
    # -e '/type of data/a patient rotation := supine' \
    invert_axis x ${base}_flip_x.hv ${base}.hv
    invert_axis z ${base}.hv ${base}_flip_x.hv
    rm ${base}_flip_x.*v
done

stir_math ../PETRIC/VOI_whole_object.hv phantom.hv
stir_math ../PETRIC/VOI_background.hv background.hv
for r in 1 4 7; do
   stir_math ../PETRIC/VOI_${r}.hv VOI${r}_ds.hv
done
