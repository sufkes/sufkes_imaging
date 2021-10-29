#!/usr/bin/env python

# This script is intended for use with FSL's fMRI motion-corretion script 'mcflirt'. 
# When 'mcflirt' is run with the flag '-mats', it saves a affine transformation matrix (default is 6 DOF which is translation + presumably rotation) required to go from each volume to the reference volume (which, by default), is the middle-timepoint volume

import os, sys
import argparse

import glob
import numpy as np
#import pprint

def getMatrixList(in_dir):
    file_list = sorted(glob.glob(in_dir+'/*'))
    matrix_list = []
    for path in file_list:
        with open(path,'rb') as handle:
            mat = np.loadtxt(handle)
            matrix_list.append(mat)
    return matrix_list

#def getDistanceList(matrix_list): # written for a list of transformation matrices.
#    distance_list = []
#    for mat in matrix_list:
#        distance = np.sqrt(np.sum(np.power(mat[:3,3],2)))
#        distance_list.append(distance)
#    return distance_list

def getDistanceList(in_path):
    with open(in_path, 'rb') as handle:
        motion_lines = np.loadtxt(handle)

    distance_list = np.zeros(shape=(motion_lines.shape[0],1),dtype=np.float)
    distance_list_rot = np.zeros(shape=(motion_lines.shape[0],1),dtype=np.float)
    for row_index in range(motion_lines.shape[0]): # loop over volumes
        motion_line = motion_lines[row_index,:]
        distance = np.sqrt(np.sum(np.power(motion_line[3:],2)))
 #       distance_list[row_index,0] = distance
    
        rotations = motion_line[:3]
        # Assume a newborn baby brain is a sphere with radius 44mm.
        delta_x = 3.0/4.0*44.0*np.abs(rotations[0])
        delta_y = 3.0/4.0*44.0*np.abs(rotations[1])
        delta_z = 3.0/4.0*44.0*np.abs(rotations[2])

#        print motion_line
#        print distance, delta_x, delta_y, delta_z
        additive_total = distance + delta_x + delta_y + delta_z
        max_individual = np.max([distance, delta_x, delta_y, delta_z])
#        distance_list[row_index,0] = additive_total
        distance_list[row_index,0] = distance


    return distance_list

def reportMotion(distance_list, thres, rate):
    num_excess = 0
    num_vol = len(distance_list)
    for distance in distance_list:
        if (distance > thres):
            num_excess += 1
    rate_excess = float(num_excess)/float(num_vol)
    print "Threshold translation distance           :", thres
    print "Number of volumes                        :", num_vol
    print "Number of volumes exceeding threshold    :", num_excess
    print "Proportion of volumes exceeding threshold:", rate_excess
    if (rate_excess <= rate):
        print "Status: Pass"
    else:
        print "Status: Fail"
    return

if (__name__ == '__main__'):
    ## Handle arguments.
    # Create argument parser
    description = """Description of function"""
    epilog = '' # """Text to follow argument explantion """
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    
    # Define positional arguments.
#    parser.add_argument("in_dir", help="path to directory containing affine transformation matrices for each volumne in a fMRI series, generated by running FSL's 'mcflirt' function with the '-mats' flag.", type=str)
    parser.add_argument("in_path", help="path to the .par by running FSL's 'mcflirt' function with the '-plots' flag.", type=str)
    
    # Define optional arguments.
#    parser.add_argument("-n", "--name", help="Subject ID to set PatientName tags to", type=str)
#    parser.add_argument("-b", "--backup", help="add an option for backup. Do not back up by default.")
#    parser.add_argument("-l", "--level", type=int, default=2, choices=[1,2,3], help="Set degree of anonymization (1: directly identifying information such as patient name, birth date, address, phone number. 2 (default): indirectly identifying information such as weight, age, physicians etc. 3: information about institution which performed scan, such as address, department etc.)")
#    parser.add_argument('-m', "--modify_pid", help="Change PatientID to specified Subject ID. Default: False", action="store_true")
#    parser.add_argument('-p', '--print-only', help='Print PHI-containing tags. Do not anonymize.', action='store_true')
#    parser.add_argument('-r', '--recursive', action='store_true', help='if in_path is a directory, find and anononymize all files in that directory.')

    parser.add_argument('-t', '--thres', help='displacement threshold in mm; count number of volumes with a larger displacement than this', action='store', type=float, default=2.0)
    parser.add_argument('-r', '--rate', help='maximum proportion of volumes which may exceed the threshold displacement before image is considered unusable', action='store', type=float, default=0.33)
                      
    # Print help if no args input.
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit()

    # Parse arguments.
    args = parser.parse_args()

    ## Main program
    # Generate list of matrices in order.
#    matrix_list = getMatrixList(args.in_dir)

    # Generate list of translation distances.
    distance_list = getDistanceList(args.in_path)

    # Print motion report.
    reportMotion(distance_list, args.thres, args.rate)
    
