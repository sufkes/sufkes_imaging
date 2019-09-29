#!/usr/bin/env python
import os, sys
import re
import string
import subprocess
import datetime
import argparse

program_name = 'processDicom.py'

# Defining dcm header names and tags
lut_tag  = {}
lut_tag['StudyDate'] = '0008,0020'
#lut_tag['StudyTime'] = '0008,0030' # Doesn't appear to be used anywhere.
lut_tag['SeriesNum'] = '0020,0011'
#lut_tag['StudyDescription'] = '0008,1030'
#lut_tag['ProtocolName'] = '0018,1030'
lut_tag['InstanceNumber'] = '0020,0013'
lut_tag['SeriesDescription'] = '0008,103e'
lut_tag['PatientName'] = '0010,0010'
lut_tag['StudyInstanceUID'] = '0020,000d'
lut_tag['SeriesInstanceUID'] = '0020,000e'

# Define characters to be used in file names (, and modified dicom tags?)
# Anything not in this group is removed.
valid_chars = '-_%s%s' % (string.ascii_letters, string.digits)

lut_value = {}# dict for storing header values

def run_cmd(sys_cmd, debug, verbose):
# one line call to output system command and control debug state
    if verbose:
        print sys_cmd
    if not debug:
        p = subprocess.Popen(sys_cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        return output, errors
    else:
        return '','' 

def clean_tag_value(tag_value):
    tag_value = tag_value.strip()
    tag_value = tag_value.replace(' ','-')   # replace spaces with -  12/05/30 - WL - Custom
    tag_value = tag_value.replace('.','-')   # replace . with -       12/05/30 - WL - Custom
    tag_value = tag_value.replace('/','-')   # replace / with -
    tag_value = tag_value.replace('\'','-')   # replace \ with - # SKU 2019-02-01: I think this replaces ' with -
    tag_value = tag_value.replace('\\','_')  # SKU 2019-02-08 - replace \ with -
    tag_value = tag_value.replace('*','s')   # replace * with s
    tag_value = tag_value.replace('?','q')   # replace ? with q
    tag_value = ''.join(c for c in tag_value if c in valid_chars) # scrub bad characters
    tag_value = re.sub("-+", "-", tag_value) # convert 001-foo---series into 001-foo-series
    tag_value = tag_value.rstrip("-")
    return tag_value

if (__name__ == '__main__'):
    # Create argument parser.
    description = '''Sort DICOM files into directories based on tags in header files.
Optionally, modify or anonymize DICOM tags. The script takes a single DICOM file as
input. To sort a directory containing many DICOM files, do
find /path/to/dir/ -type f | while read d; do processDicom.py "$d"; done
'''
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)

    # Define positional arguments. 
    parser.add_argument("in_file", help="path to DICOM file to be sorted")
    parser.add_argument("out_dir", help="directory where sorted DICOM file will be placed")

    # Define optional arguments.
    parser.add_argument("-c", "--clobber", action="store_true", dest="clobber", help="Overwrite output file")
    parser.add_argument("-m", "--move", action="store_true", dest="move", help="Move instead of copy.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="verbose output")
    parser.add_argument("--debug", action="store_true", dest="debug", help="debug mode")
    parser.add_argument("-e", "--extension", dest="extension", default="dcm", help="file extension [Default:  dcm]")

    # Steven Ufkes new arguments
    parser.add_argument("-i", "--visit_id", help="Visit ID to append to Subject ID in Study directory name. [Default: None]", type=str)
    parser.add_argument("-o", "--omit_study_uid", help="Do not include StudyInstanceUID in the Study directory name.", action="store_true")
    parser.add_argument("-t", "--omit_series_uid", help="Do not include SeriesInstanceUID in the series directory name.", action="store_true")
    parser.add_argument("-s", "--substitute_tag", help="Use alternate tags in script. E.g. '--switch_tag 0008,103e 0018,1030' will treat ProtocolName as SeriesDescription. Re-enter flag for each substitution. Useful if, e.g., PatientName is empty, but PatientID stores the Subject ID.", nargs=2, action="append", type=str, metavar=('old_tag', 'new_tag'))
    parser.add_argument("-n", "--subject_id", help="Custom Subject ID to be used in Study directory name. By default, the PatientName dicom tag (0010,0010) is used.", type=str)
    parser.add_argument("-d", "--study_date", help="Custom Study Date to be used in Study directory name. By default, the StudyDate dicom tag (0008,0020) is used.", type=str)
    parser.add_argument("-f", "--rename_file", help="Rename file according to it's InstanceNumber tag and append '.dcm'. By default, only append '.dcm'.", action='store_true')
    parser.add_argument("-r", "--recursive", action="store_true")


    # Print help if no args input.
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit()

    # Parse input arguments and store them.
    args = parser.parse_args()


    # Check that file exists
    if (not os.path.exists(args.in_file)):
        print "Input file does not exist."
        sys.exit()

    # Quit if file is not DICOM.
    cmd_file = 'file "%s"' % (args.in_file)
    output, errors = run_cmd(cmd_file, 0, 0)
    if (not "DICOM" in output):
        print "Error: File might not be DICOM: %s" % (args.in_file)
        sys.exit()

    # Determine what type of operation to carry out
    if args.move:
        operation = 'mv'
    else:
        operation = 'cp'

    # Steven Ufkes - Use alternate tags if specified.
    if (args.substitute_tag != None):
#        print "Old lut_tag:"
#        print lut_tag
        for pair in args.substitute_tag:
            for tag_name in lut_tag:
                if (lut_tag[tag_name] == pair[0]):
                    lut_tag[tag_name] = pair[1]
                    break
#        print "New lut_tag:"
#        print lut_tag
                        
    
    # Check scanner type (0008,0070 - Manufacturer tag)
    cmd_dcmdump = 'dcmdump "%s" | grep 0008,0070' % (args.in_file)
    output, errors = run_cmd(cmd_dcmdump, 0, 0)
    if string.lower(output).find('philips') > 0:
        scanner_type = 'philips'
    elif string.lower(output).find('siemens'):
        scanner_type = 'siemens'
    elif string.lower(output).find('ge'):
        scanner_type = 'ge'
    else:
        scanner_type = 'other'

    for tag_name in lut_tag:
        if (args.subject_id != None) and (tag_name == "PatientName"): # if manually specifying PatientName
            tag_value = args.subject_id
        elif (args.study_date != None) and (tag_name == "StudyDate"): # if manually specifying StudyDate
            tag_value = args.study_date
        else:
            # Dump dcmheader and grap header line
            cmd_dcmdump = 'dcmdump "%s" | grep %s' % (args.in_file, lut_tag[tag_name])
            output, errors = run_cmd(cmd_dcmdump, 0, 0)
#            print cmd_dcmdump
#            print output
            if (scanner_type == 'philips') and (tag_name == 'InstanceNumber'): # Check if Philips type dicom and looking for InstanceNumber
                for line in output.split('\n'): # Split output into separate lines
                    if (not line=='') and (line.find('[0]') == -1): # Ignore all lines without 'real' instance information
                        output = line

            # Steven Ufkes - general check for multiple tags
            elif (len(output.split('\n')) > 2): 
                print "Warning: Multiple values found for tag "+tag_name+" in file "+args.in_file
                print output
                for line in output.split('\n'):    
                    if (not line=='') and (line.find('(no value available)') == -1): # Ignore all lines without 'real' instance information; Use first line found with data.
                        output = line
                        break
                print "Using value: "+output.split('[')[1].split(']')[0]
    
            # Custom error check for missing tags - Steven Ufkes 2018-11-16
            try: 
                tag_value = output.split('[')[1].split(']')[0]    # Grab value between [ ]
#                tag_value = clean_tag_value(tag_value)
            except IndexError:
                print "Warning: Unknown DICOM tag: "+tag_name+" in file "+os.path.join(args.in_file)
                tag_value = "Unknown"+tag_name
        # Replace bad characters
        tag_value = clean_tag_value(tag_value)

        # Store tag value
        lut_value[tag_name] = tag_value

    # Write Study directory name (e.g. 20070214_SK010004_V02).
    # StudyDate
#    if (args.study_date == None):
    dir_base = lut_value['StudyDate']
#    else:
#        dir_base = clean_tag_value(args.study_date)
    # Subject ID
#    if (args.subject_id == None):
    dir_base += "_" + lut_value['PatientName']
#    else:
#        dir_base += "_" + clean_tag_value(args.subject_id)
    # Visit ID
    if (args.visit_id != None):
        dir_base += "_" + clean_tag_value(args.visit_id)
    # StudyInstanceUID
    if (not args.omit_study_uid):
        dir_base += "_" + lut_value['StudyInstanceUID']        

    dir_base_full = os.path.join(args.out_dir, dir_base)

    if (not os.path.exists(dir_base_full)):
        cmd_mkdir = 'mkdir "%s"' % (dir_base_full)
        output, errors = run_cmd(cmd_mkdir, args.debug, args.verbose)

    try:
        if (args.omit_series_uid):
            dir_series = '%03.d-%s' % (int(lut_value['SeriesNum']), lut_value['SeriesDescription'])
        else:
            dir_series = '%03.d-%s-UID_%s' % (int(lut_value['SeriesNum']), lut_value['SeriesDescription'], lut_value['SeriesInstanceUID'])
    except ValueError:
        if (args.omit_series_uid):
            dir_series = '%s-%s' % (lut_value['SeriesNum'], lut_value['SeriesDescription'])
        else:
            dir_series = '%s-%s-UID_%s' % (lut_value['SeriesNum'], lut_value['SeriesDescription'], lut_value['SeriesInstanceUID'])
    dir_series_full = os.path.join(dir_base_full, dir_series)

    if (not os.path.exists(dir_series_full)):
        cmd_mkdir = 'mkdir "%s"' % (dir_series_full)
        output, errors = run_cmd(cmd_mkdir, args.debug, args.verbose)

    if (args.rename_file):
        try:
            fname_out = '%04.d' % (int(lut_value['InstanceNumber']))
        except ValueError:
            fname_out = '%s' % (lut_value['InstanceNumber'])
    else:
        fname_out = os.path.basename(args.in_file)
        if (fname_out[-4:] == '.dcm'):
            fname_out = fname_out[:-4]

    full_out = '%s.%s' % (os.path.join(dir_series_full, fname_out), args.extension)
    
# If Siemens scanner, check for possibility of Mag/Ph type output, where files will have the same 
# instance number (leading to the same destination file name) but different echo numbers (0018,0086)
# This problem does not appear to exist on GE and Philips scanners (which have different echo #s and
# instance #s
    if (args.rename_file):
        if scanner_type  == 'siemens':
            # get source echo number
            cmd_dcmdump = 'dcmdump %s | grep 0018,0086' % (args.in_file)
            output, errors = run_cmd(cmd_dcmdump, 0, 0)
            if (output != ''):
                echo_number_source = int(output.split('[')[1].split(']')[0])
            else:
                echo_number_source = 1
            if (echo_number_source > 1):   # append echo number if it's >1
                # if non-suffixed file exists (ie. echo number = 1) then add suffix
                if (os.path.exists(full_out)):
                    if (args.verbose):
                        print 'Renaming destination file - first echo'
                    fname_new = '%s_01.%s' % (os.path.splitext(full_out)[0], args.extension)
                    cmd_mvdest = 'mv %s %s' % (full_out, fname_new)
                    output, errors = run_cmd(cmd_mvdest, args.debug, args.verbose)
                    if errors == '':
                        cmd_rmorig = 'rm %s' % (full_out)
                        output, errors = run_cmd(cmd_rmorig, args.debug, args.verbose)
                fname_out = '%s_%02.d' % (fname_out, echo_number_source)
    #            full_out = '%s/%s/%s/%s.%s' % \
    #                (dir_output, dir_base, dir_series, fname_out, extension)
                full_out = '%s.%s' % (os.path.join(dir_series_full, fname_out), args.extension)
            else:
                # if new file
                if (not os.path.exists(full_out)):
    #                dir_full_out = '%s/%s/%s' % (dir_output, dir_base, dir_series) # same as dir_series_full ?
                    list_existing = str(os.listdir(dir_series_full))
                    # check if basic filename already exists
                    if (list_existing.find(fname_out) > -1): 
                        fname_out = '%s_01' % (fname_out,)
    #                full_out = '%s/%s/%s/%s.%s' % \
    #                    (dir_output, dir_base, dir_series, fname_out, extension)
                    full_out = '%s.%s' % (os.path.join(dir_series_full, fname_out), args.extension)

    if args.clobber:
        cmd_mvdcm = '%s "%s" "%s"' % (operation, args.in_file, full_out)
        overwrite_completed = os.path.exists(full_out) # *Could fail to detect overwrite due to race condition.
        output, errors = run_cmd(cmd_mvdcm, args.debug, args.verbose)     # Copying DCM with new name
    else:
        operation_completed = False
        cmd_overwrite_attempt = None
        while (not operation_completed):
            try:
                cmd_mvdcm = '%s "%s" "%s"' % (operation, args.in_file, full_out) # overwrite temp file with dicom file
		os.open(full_out, os.O_CREAT|os.O_EXCL) # create empty temp file at destination path
                output, errors = run_cmd(cmd_mvdcm, args.debug, args.verbose) # Copying DCM with new name
                operation_completed = True
            except OSError:
                if (cmd_overwrite_attempt == None): # If this is the first overwrite attempt for this file.
                    cmd_overwrite_attempt = cmd_mvdcm # Store the first overwrite attempt command for the log.
                fname_out = fname_out + 'A'
                full_out = '%s.%s' % (os.path.join(dir_series_full, fname_out), args.extension)

