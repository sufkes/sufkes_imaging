#!/usr/bin/env python3

import os
import sys
import argparse

import numpy as np
import nibabel as nib

def main(image_in, image_out, bval_in, bval_out, bvec_in, bvec_out, volumes):
    ## Image
    if image_in:
        image_nifti = nib.load(image_in)
        image_array = image_nifti.get_fdata()
        image_array_modified = np.delete(image_array, volumes, axis=3)
        image_nifti_modified = nib.Nifti1Image(image_array_modified, image_nifti.affine, header=image_nifti.header)
        nib.save(image_nifti_modified, image_out)

    ## Bval file
    if bval_in:
        bval_array = np.loadtxt(bval_in)
        bval_array_modified = np.delete(bval_array, volumes)
        bval_array_modified = np.expand_dims(bval_array_modified, axis=0)
        np.savetxt(bval_out, bval_array_modified, delimiter=' ', fmt='%.10g')
        
    ## Bvec file
    if bvec_in:
        bvec_array = np.loadtxt(bvec_in)
        bvec_array_modified = np.delete(bvec_array, volumes, axis=1)
        np.savetxt(bvec_out, bvec_array_modified, delimiter='  ', fmt='%.10g')
    return

if (__name__ == '__main__'):
    # Create argument parser.
    description = '''Input a DTI series or associated data (bvec file, or bval file), and remove specified volumes/time points from the inputs.'''
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Define positional arguments.
#    parser.add_argument('', help='')
    
    # Define optional arguments.
    parser.add_argument('--image_in', type=str, help='path to input DTI NIFTI file')
    parser.add_argument('--image_out', type=str, help='path to output DTI NIFTI file')
    parser.add_argument('--bval_in', type=str, help='path to input bval file, as generated by dcm2niix')
    parser.add_argument('--bval_out', type=str, help='path to output bval file, as generated by dcm2niix')
    parser.add_argument('--bvec_in', type=str, help='path to input bvec file, as generated by dcm2niix')
    parser.add_argument('--bvec_out', type=str, help='path to output bvec file, as generated by dcm2niix')
    parser.add_argument('-v', '--volumes', type=int, nargs='*', metavar=('VOLUME_1', 'VOLUME_2'), help='volumes to be removed from DTI series, where the first volume has index 0.')

    # Print help if no arguments input.
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit()

    # Parse arguments.
    args = parser.parse_args()

    # Run main function.
    main(**vars(args))
