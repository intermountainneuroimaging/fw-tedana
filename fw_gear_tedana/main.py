"""Main module."""

import logging
import os
import os.path as op
import glob
from pathlib import Path
from typing import List, Tuple
import subprocess as sp
import numpy as np
import pandas as pd
import sys
import re
import shutil
import tempfile
from collections import OrderedDict
from zipfile import ZIP_DEFLATED, ZipFile
import errorhandler
from typing import List, Tuple, Union
import json
from flywheel_gear_toolkit.utils.zip_tools import zip_output
from flywheel_gear_toolkit.interfaces.command_line import (
    build_command_list
)

from utils.command_line import exec_command
from utils.zip_htmls import zip_htmls

log = logging.getLogger(__name__)

# Track if message gets logged with severity of error or greater
error_handler = errorhandler.ErrorHandler()

# # Also log to stderr
# stream_handler = logging.StreamHandler(stream=sys.stderr)
# log.addHandler(stream_handler)


def prepare(
        gear_options: dict,
        app_options: dict,
) -> Tuple[List[str], List[str]]:
    """Prepare everything for the algorithm run.

    It should:
     - Install FreeSurfer license (if needed)

    Same for FW and RL instances.
    Potentially, this could be BIDS-App independent?

    Args:
        gear_options (Dict): gear options
        app_options (Dict): options for the app

    Returns:
        errors (list[str]): list of generated errors
        warnings (list[str]): list of generated warnings
    """
    # pylint: disable=unused-argument
    # for now, no errors or warnings, but leave this in place to allow future methods
    # to return an error
    errors: List[str] = []
    warnings: List[str] = []

    return errors, warnings
    # pylint: enable=unused-argument


def run(gear_options: dict, app_options: dict) -> int:
    """launch workflow for fmriprep or manual inputs.

    Arguments:
        gear_options: dict with gear-specific options
        app_options: dict with options for the BIDS-App

    Returns:
        run_error: any error encountered running the app. (0: no error)
    """

    log.info("This is the beginning of the run file")

    # Loop through tasks if fmriprep is passed as input
    if app_options["inputtype"] == "fmriprep":
        run_error = run_fmriprep_pipe(gear_options, app_options)

    else:
        run_error = run_manual_pipe(gear_options, app_options)

    return run_error


def run_fmriprep_pipe(gear_options: dict, app_options: dict) -> int:
    """Run tedana using fmriprep inputs.

    Arguments:
        gear_options: dict with gear-specific options
        app_options: dict with options for the BIDS-App

    Returns:
        run_error: any error encountered running the app. (0: no error)
    """

    path = op.join(gear_options["fmriprep-dir"], "sub-" + app_options["sid"], "ses-" + app_options["sesid"])
    tasks = fmriprep_get_tasks(path)

    # run tedana workflow for each task
    for task in tasks:
        echo_files = fmriprep_get_echos(path, task)

        if '' in echo_files:
            continue

        # pull echo time from .json
        echo_times = [];
        arg_options = dict()
        for e in echo_files:
            with open(e.replace("nii.gz", "json")) as f:
                dat = json.load(f)
                echo_times.append(dat["EchoTime"] * 1000)

        log.info("Using multiecho files: %s", "\n".join(echo_files))
        log.info("Using echo times (ms): %s", str(echo_times))

        arg_options["d"] = " ".join(echo_files)
        arg_options["e"] = " ".join([str(i) for i in echo_times])

        index = [idx for idx, s in enumerate(echo_files[0].split("/")[-1].split("_")) if 'echo' in s][0]
        arg_options["prefix"] = "_".join(echo_files[0].split("/")[-1].split("_")[0:index])

        if app_options["explicit-mask"]:
            f = searchfiles(app_options["prefix"] + "_desc-brain_mask.nii.gz")
            arg_options["mask"] = f[0]
            log.info("Explicit mask requested using file: %s", f[0])

        if app_options["output-layout"] == "bids":
            output_analysis_id_dir = op.join(gear_options["work-dir"], gear_options["destination-id"], "fmriprep",
                                             "derivatives", "tedana", "sub-" + app_options["sid"],
                                             "ses-" + app_options["sesid"], "func")
            os.makedirs(output_analysis_id_dir, exist_ok=True)
            arg_options["out-dir"] = output_analysis_id_dir
        else:
            output_analysis_id_dir = op.join(gear_options["work-dir"], gear_options["destination-id"], "fmriprep",
                                             "sub-" + app_options["sid"], "ses-" + app_options["sesid"], "func")
            os.makedirs(output_analysis_id_dir, exist_ok=True)
            arg_options["out-dir"] = output_analysis_id_dir

        arg_options["command-line-args"] = app_options["command-line-args"]

        # generate command
        command = generate_command(gear_options, arg_options)

        if error_handler.fired:
            log.critical('Failure: exiting with code 1 due to logged errors')
            run_error = 1
            return run_error

        # This is what it is all about
        stdout, stderr, run_error = exec_command(
            command,
            dry_run=gear_options["dry-run"],
            shell=True,
            cont_output=True,
            cwd=gear_options["work-dir"]
        )

        # if gear completed without error, move report to also contain acq prefix
        if run_error == 0:
            files = searchfiles(os.path.join(arg_options["out-dir"], "tedana*"), dryrun=False)
            for f in files:
                f = Path(f)
                if arg_options["prefix"] in f.name:
                    continue
                os.rename(str(f), str(f).replace("tedana", arg_options["prefix"]))

            # Make archives for result *.html files for easy display on platform
            zip_htmls(gear_options["output-dir"], gear_options["destination-id"], output_analysis_id_dir)

    if not gear_options["dry-run"]:
        # zip outputs
        zipname = "tedana_" + app_options["sesid"] + "_" + gear_options["destination-id"]
        cmd = "zip -r " + os.path.join(gear_options["output-dir"], zipname) + ".zip " + gear_options["destination-id"]
        execute_shell(cmd, dryrun=gear_options["dry-run"], cwd=gear_options["work-dir"])

        # Make archives for result *.html files for easy display on platform
        zip_htmls(gear_options["output-dir"], gear_options["destination-id"], output_analysis_id_dir)

    return run_error


def run_manual_pipe(gear_options: dict, app_options: dict) -> int:
    """Run tedana using manual inputs.

    Arguments:
        gear_options: dict with gear-specific options
        app_options: dict with options for the BIDS-App

    Returns:
        run_error: any error encountered running the app. (0: no error)
    """

    # TODO write this method!

    log.info("manual input run not currently supported")
    pass


def fmriprep_get_tasks(path):

    # search for all func "bold.nii.gz" func files to choose from..
    results = []
    files = searchfiles(os.path.join(path,"func","*echo*bold.nii.gz"))
    for f in files:
        index1 = [idx for idx, s in enumerate(f.split("/")[-1].split("_")) if 'task' in s][0]
        index2 = [idx for idx, s in enumerate(f.split("/")[-1].split("_")) if 'echo' in s][0]
        res = "_".join(f.split("/")[-1].split("_")[index1:index2])

        results.append(res)

    return list(set(results))


def fmriprep_get_echos(path, task):

    files = searchfiles(os.path.join(path, "func", "*" + task + "*echo*desc-preproc_bold.nii.gz"))
    return files


def generate_command(
        gear_options: dict,
        app_options: dict,
) -> List[str]:
    """Build the main command line command to run.

    This method should be the same for FW and XNAT instances. It is also BIDS-App
    generic.

    Args:
        gear_options (dict): options for the gear, from config.json
        app_options (dict): options for the app, from config.json
    Returns:
        cmd (list of str): command to execute
    """

    cmd = []
    cmd.append(gear_options["tedana"]["common_command"])

    skip_pattern = re.compile("gear-|lsf-|slurm-|singularity-")

    command_parameters = {}
    log_to_file = False
    for key, val in app_options.items():

        # these arguments are passed directly to the command as is
        if key == "command-line-args" and val:
            bids_app_args = val.split(" ")
            for baa in bids_app_args:
                cmd.append(baa)

        elif not skip_pattern.match(key):
            command_parameters[key] = val

    # Validate the command parameter dictionary - make sure everything is
    # ready to run so errors will appear before launching the actual gear
    # code.  Add descriptions of problems to errors & warnings lists.
    # print("command_parameters:", json.dumps(command_parameters, indent=4))

    cmd = build_command_list(cmd, command_parameters)


    return cmd


def execute_shell(cmd, dryrun=False, cwd=os.getcwd()):
    log.info("\n %s", cmd)
    if not dryrun:
        terminal = sp.Popen(
            cmd,
            shell=True,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            universal_newlines=True,
            cwd=cwd
        )
        stdout, stderr = terminal.communicate()
        log.debug("\n %s", stdout)
        log.debug("\n %s", stderr)

        return stdout


def searchfiles(path, dryrun=False) -> list[str]:
    cmd = "ls -d " + path

    log.debug("\n %s", cmd)

    if not dryrun:
        terminal = sp.Popen(
            cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True
        )
        stdout, stderr = terminal.communicate()
        log.debug("\n %s", stdout)
        log.debug("\n %s", stderr)

        files = stdout.strip("\n").split("\n")
        return files


