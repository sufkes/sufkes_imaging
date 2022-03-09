# imaging_tools
Scripts for various image processing tasks

## How to run scripts (for Miller lab members)
Members of the Miller lab with an RIT-HPC account should be able to run these scripts on HPC in interactive sessions or batch scripts, after running the following command:

```source /hpf/largeprojects/smiller/tools/python_environments/activate_py3env.sh```

This will load the required HPC modules, activate a Python environment with the required packages installed, and add the script directories to your `$PATH` variable so that they can be run by name.

## Available tools
Scripts that do not have an entry in this list may not work yet.
### `dicom/` - Tools for processing DICOM files
* `processDicom.py` - Sort DICOM files into directories.
  * Run `processDicom.py -h` for usage.
* `anonDicom.py` - Deidentify DICOM files.
  * Run `anonDicom.py -h` for usage.
### `dti/` - Tools for processing and analyzing diffusion tensor imaging data
### `fmri/` - Tools for processing and analyzing functional MRI data
### `misc/` - Tools for miscellaneous image processing tasks
* `roiStats.py` - Report statistics on size and extent of region of interest clusters in 3D images.
  * Run `roiStats.py -h` for usage.
  * For examples, see `/hpf/largeprojects/smiller/examples/lesion_extent/README.txt` on HPC.
### `old_scripts/` - Old scripts that are kept for reference.

## Requirements
The following software is required. All packages are already installed on HPC and can be activated as described above.
* Python 3.9
* Python 2.7 (for some old scripts).
* Python packages:
  * numpy
  * scipy
  * matplotlib
  * pandas
  * pydicom
  * pyminc
  * nibabel
  * natsort
  * bctpy
  * sklearn
  * nilearn
  * scikit-image
* DCMTK (https://dicom.offis.de/index.php.en)
* FSL (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation)
* MINC Toolkit (https://bic-mni.github.io)
* ANTs (https://github.com/ANTsX/ANTs)