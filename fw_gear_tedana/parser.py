"""Parser module to parse gear config.json."""
from typing import Tuple
from zipfile import ZipFile
from flywheel_gear_toolkit import GearToolkitContext
import os
import logging
import glob
import subprocess as sp
from pathlib import Path
from fw_gear_tedana.main import searchfiles


log = logging.getLogger(__name__)


def parse_config(
        gear_context: GearToolkitContext,
) -> Tuple[dict, dict]:
    """Parse the config and other options from the context, both gear and app options.

    Returns:
        gear_options: options for the gear
        app_options: options to pass to the app
    """
    # ##   Gear config   ## #

    gear_options = {
        "dry-run": gear_context.config.get("gear-dry-run"),
        "output-dir": gear_context.output_dir,
        "destination-id": gear_context.destination["id"],
        "work-dir": gear_context.work_dir,
        "client": gear_context.client,
        "environ": os.environ,
        "debug": gear_context.config.get("debug"),
    }

    # set the output dir name for the BIDS app:
    gear_options["output_analysis_id_dir"] = (
            gear_options["output-dir"] / gear_options["destination-id"]
    )

    # ##   App options:   ## #
    app_options_keys = [
        "echo-times",
        "output-layout",
        "explicit-mask",
        "command-line-args"
    ]
    app_options = {key: gear_context.config.get(key) for key in app_options_keys}

    work_dir = gear_options["work-dir"]
    if work_dir:
        app_options["work-dir"] = work_dir

    if gear_context.get_input_path("fmriprep_zip") and not gear_context.get_input_path("fmri_echo_1"):
        app_options["inputtype"] = "fmriprep"
        gear_options["fmriprep_zipfile"] = gear_context.get_input_path("fmriprep_zip")
        log.info("Inputs file path, %s", gear_options["fmriprep_zipfile"])

        with ZipFile(gear_options["fmriprep_zipfile"], "r") as f:
            fmriprep_anlys_id = [item.split('/')[0] for item in f.namelist()][0]

        # unzip preproc folder and reorganize
        unzip_file(gear_options, gear_options["fmriprep_zipfile"])

        gear_options["fmriprep-dir"] = os.path.join(gear_options["work-dir"], fmriprep_anlys_id, "fmriprep")

    elif gear_context.get_input_path("fmri_echo_1") and not gear_context.get_input_path("fmriprep_zip"):
        app_options["inputtype"] = "manual"
        gear_options["fmri_echo_1_file"] = gear_context.get_input_path("fmri_echo_1")
        log.info("Inputs file path, %s", gear_options["fmri_echo_1_file"])

        if gear_context.get_input_path("fmri_echo_2"):
            gear_options["fmri_echo_2_file"] = gear_context.get_input_path("fmri_echo_2")
            log.info("Inputs file path, %s", gear_options["fmri_echo_2_file"])

        if gear_context.get_input_path("fmri_echo_3"):
            gear_options["fmri_echo_3_file"] = gear_context.get_input_path("fmri_echo_3")
            log.info("Inputs file path, %s", gear_options["fmri_echo_3_file"])

    else:
        log.error("No inputs or inputs mismatch passed. Cannot proceed. Exiting.")

    # pull config settings
    gear_options["tedana"] = {
        "common_command": "tedana",
        "params": ""
    }

    destination = gear_context.client.get(gear_context.destination["id"])
    sid = gear_context.client.get(destination.parents.subject)
    sesid = gear_context.client.get(destination.parents.session)

    app_options["sid"] = sid.label
    app_options["sesid"] = sesid.label

    return gear_options, app_options


def unzip_file(gear_options, zip_filename):
    """
    unzip_file unzips the contents of zipped gear output into the working
    directory.
    Args:
        gear_options: The gear context object
            containing the 'gear_dict' dictionary attribute with key/value,
            'gear-dry-run': boolean to enact a dry run for debugging
        zip_filename (string): The file to be unzipped
    """
    z = ZipFile(zip_filename, "r")
    log.info("Unzipping zipped directory contents, %s", zip_filename)

    z.extractall(gear_options["work-dir"])
    log.info(f'Unzipped the file to {gear_options["work-dir"]}')
