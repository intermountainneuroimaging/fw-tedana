"""Compress HTML files."""

import datetime
import glob
import logging
import os
import subprocess as sp
from pathlib import Path
from bs4 import BeautifulSoup
import base64
import re

FWV0 = Path.cwd()
log = logging.getLogger(__name__)


def zip_it_zip_it_good(output_dir, destination_id, name, path):
    """Compress html file into an appropriately named archive file *.html.zip
    files are automatically shown in another tab in the browser. These are
    saved at the top level of the output folder."""

    name_no_html = name[:-5]  # remove ".html" from end

    dest_zip = os.path.join(
        output_dir, name_no_html + "_" + destination_id + ".html.zip"
    )

    log.debug('Creating viewable archive "' + dest_zip + '"')

    command = ["zip", "-q", "-r", dest_zip, "index.html"]

    # find all directories called 'figures' and add them to the archive
    for root, dirs, files in os.walk(path):
        common_prefix = os.path.commonprefix([path, root])
        relpath = os.path.relpath(root, common_prefix)

        for name in dirs:
            if name == "figures":
                figures_path = os.path.join(relpath, "figures")
                command.append(figures_path)
                log.info(f"including {figures_path}")

    # log command as a string separated by spaces
    log.debug(f"pwd = %s", Path.cwd())
    log.debug(" ".join(command))

    result = sp.run(command, check=True)


def zip_htmls(output_dir, destination_id, path):
    """Zip all .html files at the given path so they can be displayed
    on the Flywheel platform.
    Each html file must be converted into an archive individually:
      rename each to be "index.html", then create a zip archive from it.
    """

    log.info("Creating viewable archives for all html files")

    if os.path.exists(path):

        log.debug("Found path: " + str(path))

        os.chdir(path)

        html_files = glob.glob("*.html")

        if len(html_files) > 0:

            # if there is an index.html, do it first and re-name it for safe
            # keeping
            save_name = ""
            if os.path.exists("index.html"):
                log.info("Found index.html")
                zip_it_zip_it_good(output_dir, destination_id, "index.html", path)

                now = datetime.datetime.now()
                save_name = now.strftime("%Y-%m-%d_%H-%M-%S") + "_index.html"
                os.rename("index.html", save_name)

                html_files.remove("index.html")  # don't do this one later

            for h_file in html_files:
                log.info("Found %s", h_file)



                # os.rename(h_file, "index.html")
                name_no_html = Path(h_file).name[:-5]  # remove ".html" from end

                dest_html = os.path.join(
                    output_dir, name_no_html + "_" + destination_id + ".html"
                )

                flatten_image_refs(h_file, dest_html)  # outputs flattened file as "index.html"

                # zip_it_zip_it_good(output_dir, destination_id, h_file, path)
                # os.rename("index.html", h_file)

            # restore if necessary
            if save_name != "":
                os.rename(save_name, "index.html")

        else:
            log.warning("No *.html files at " + str(path))

    else:

        log.error("Path NOT found: " + str(path))

    os.chdir(FWV0)

# TODO -- flatten component spatial maps

def flatten_image_refs(filename, dest_html):
    filename = Path(filename)
    with open(filename) as inf:
        txt = inf.read()
    html1 = BeautifulSoup(txt, 'html.parser')

    # look for acompanying figures directory
    if 'figures' in os.listdir(filename.parent):
        for f in os.listdir(os.path.join(filename.parent,'figures')):
            f = Path(os.path.join(filename.parent,'figures',f))
            with open(f, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                txt = txt.replace("./figures/"+f.name,
                                      "data:image/svg+xml;base64, " + encoded_string.decode('utf-8'))

    log.info("Writing html: %s", dest_html)

    with open(dest_html, "w") as outf:
        outf.write(txt)

