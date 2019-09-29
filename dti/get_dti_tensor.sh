# This script calculates the diffusion tensor for a raw DTI image. It is written to be run on the 'graphics' 
# server at SickKids, but the paths could be modified to run on other systems with fsl.
#
# Usage: ./processDTI.sh <input directory>
#
# The input directory must contain a single raw DTI image in NIFTI format (with extension *.nii or *.nii.gz), 
# a single *.bvec file, and a single *.bval file. These three files can be generated by running dcm2nii or 
# dcm2niix on a DTI series in DICOM format. The reference volume (the volume with B=0) is assumed to be 0, 
# which is ensured if the NIFTI image was created using dcm2nii or dcm2niix. If more than one NIFTI/bval/bvec
# file is found in the specified directory, the script raises an error and does nothing. 

# Load FSL; do this in interactive environment or qsub job script.
#module purge
#module load fsl
#source /hpf/tools/centos6/fsl/5.0.8/etc/fslconf/fsl.sh

# Move to target directory which contains a raw DTI in NIFTI format, a bvec file, and a bval file.
base_dir="$1"
cd $base_dir
base_dir="$PWD"
echo "$base_dir"

# Assign NIFTI, bvec, and bval files.
raw_dti=$(ls | grep 'nii')
bvec=$(ls *bvec)
bval=$(ls *bval)

if [ $(echo "$raw_dti" | wc -w) == 1 ] && [ $(echo "$bvec" | wc -w) == 1 ] && [ $(echo "$bval" | wc -w) == 1 ];
    then 
    echo "raw DTI file :" $raw_dti;
    echo "bvec file    :" $bvec;
    echo "bval file    :" $bval;
    
    # Create eddy current corrected file
#    reference_volume=0 # assume reference volume is 0 (should be if converted to NIFTI using dcm2nii or dcm2niix).
    reference_volume="$(whereIsBZero.py "$bval")"
    echo "Performing eddy current correction with b=0 reference volume" "$reference_volume"
    ecc="ecc"
#    /hpf/tools/centos6/fsl/5.0.8/bin/eddy_correct "${base_dir}/${raw_dti}" "${base_dir}/${ecc}" "${reference_volume}"
    eddy_correct "${base_dir}/${raw_dti}" "${base_dir}/${ecc}" "${reference_volume}"

    # Create brain mask for DTI data. Use fractional intensity threshold = 0.3; do not output brain-extracted image; output binary brain mask image.
    echo "Performing brain mask extraction"
    brain="_brain" # suffix for brain mask
#    /hpf/tools/centos6/fsl/5.0.8/bin/bet "${base_dir}"/"${ecc}" "${base_dir}"/"${ecc}${brain}" -f 0.3 -g 0 -n -m 
    bet "${base_dir}"/"${ecc}" "${base_dir}"/"${ecc}${brain}" -f 0.3 -g 0 -n -m 

    # Reconstruct diffusion tensor
    echo "Reconstructing diffusion tensor"
    dti="dti" # output file prefix
#    /hpf/tools/centos6/fsl/5.0.8/bin/dtifit --data="${base_dir}"/"${ecc}" --out="${base_dir}"/"${dti}" --mask="${base_dir}"/"${ecc}${brain}"_mask --bvecs="${base_dir}"/"${bvec}" --bvals="${base_dir}"/"${bval}"
    dtifit --data="${base_dir}"/"${ecc}" --out="${base_dir}"/"${dti}" --mask="${base_dir}"/"${ecc}${brain}"_mask --bvecs="${base_dir}"/"${bvec}" --bvals="${base_dir}"/"${bval}"

else
    echo "Found multiple NIFTI or bval or bvec files. Skipping directory"
fi