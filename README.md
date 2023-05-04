# Tedana
[Flywheel Gear](https://github.com/flywheel-io/gears/tree/master/spec) which runs [tedana](https://tedana.readthedocs.io/en/stable/) Long-Term Support version 0.0.12 (April 14, 2022). TE-dependent analysis (tedana) is a Python library for denoising multi-echo functional magnetic resonance imaging (fMRI) data. tedana originally came about as a part of the ME-ICA pipeline, although it has since diverged. An important distinction is that while the ME-ICA pipeline originally performed both pre-processing and TE-dependent analysis of multi-echo fMRI data, tedana now assumes that you're working with data which has been previously preprocessed.

The version number is (Flywheel gear) MAJOR . MINOR . PATCH _ (algorithm) YY . MINOR . PATCH

## Overview
Tedana shoud be used to denoise and compine multi-echo (ME) fMRI acquisitions. Preprocessing in fmriprep or another pipeline (e.g. AFNI) are supported, but the gear is streamlined for use with fmriprep preprocessed images. We suggest using fmriprep v23.0.1 or higher, with the configuration option "--me-output-echos". For questions related to preprocessing MB/ME data, review tedana [documentation](https://tedana.readthedocs.io/en/stable/).

The fw-tedana Gear must be run at a session level. 

## Setup (recommended fmriprep preprocessing):
Before running BIDS curation on your data, you must first prepare your data with the following steps:
1. On a BIDS curated dataset within Flywheel, run fmriprep (v.23.0.1^) at a session level. Check all outputs and report for data quality before proceeding. 
2. Use fmriprep preprocessed dataset (output of fmriprep gear) as the input for tedana. 

(Not Recommended) If you are choosing to preprocess the ME fMRI acquisition with an alternative processing pipeline, you may pass the preprocessed echos as individual inputs to tedana. This must be accompanied by the config parameter "echos" to specify the echo time for each individual image set.

## Inputs

This gear can be run using one of two methods: (1) hand passed multiecho images, (2) fmirprep preprocessed dataset.

### fmri_echo_1 (optional)
Alternative method to pass preprocessed fmri multi echo separately (one echo per input). First (shortest) echo.

### fmri_echo_2 (optional)
Alternative method to pass preprocessed fmri multi echo separately (one echo per input). Second (middle) echo.

### fmri_echo_3 (optional)
Alternative method to pass preprocessed fmri multi echo separately (one echo per input). Last (longest) echo.

### fmriprep_zip (optional)
Entire preprocessed session level dataset from fmriprep. Tedana will be run on all fmri ME acquisitions. "--me-output-echos" option must be selected in fmriprep processing to retain split echos in fmriprep output.

## Config:

### command-line-args (optional)
app argument: command line arguments passed directly to tedana. May be used to set additional tedana configuration settings not set directly here.

### echo-times (optional)
app argument: Space seperated list of echo times TE: e1 e2 e3. Only required if input is passed as the individual echos. Gear will interpret echo time from fmriprep outputs if passed.

### gear-log-level (optional)
Gear argument: Gear Log verbosity level (ERROR|WARNING|INFO|DEBUG)

### gear-writable-dir (optional)
Gears expect to be able to write temporary files in /flywheel/v0/. If this location is not writable (such as when running in Singularity), this path will be used instead. fMRIPrep creates a large number of files so this disk space should be fast and local.

### output-layout
Gear argument: Organizational method for outputs (BIDS | LEGACY)

### slurm-... (optional)
Slurm configuration variables uses to run job on SLRUM controlled HPC.


## Citing Tedana
If you use tedana, please cite the following papers, as well as our most recent Zenodo release:

DuPre, E. M., Salo, T., Ahmed, Z., Bandettini, P. A., Bottenhorn, K. L., Caballero-Gaudes, C., Dowdle, L. T., Gonzalez-Castillo, J., Heunis, S., Kundu, P., Laird, A. R., Markello, R., Markiewicz, C. J., Moia, S., Staden, I., Teves, J. B., Uruñuela, E., Vaziri-Pashkam, M., Whitaker, K., & Handwerker, D. A. (2021). TE-dependent analysis of multi-echo fMRI with tedana. Journal of Open Source Software, 6(66), 3669. doi:10.21105/joss.03669.
Kundu, P., Inati, S. J., Evans, J. W., Luh, W. M., & Bandettini, P. A. (2011). Differentiating BOLD and non-BOLD signals in fMRI time series using multi-echo EPI. NeuroImage, 60, 1759-1770.
Kundu, P., Brenowitz, N. D., Voon, V., Worbe, Y., Vértes, P. E., Inati, S. J., Saad, Z. S., Bandettini, P. A., & Bullmore, E. T. (2013). Integrated strategy for improving functional connectivity mapping using multiecho fMRI. Proceedings of the National Academy of Sciences, 110, 16187-16192.
