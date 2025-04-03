#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""

import logging
from os.path import dirname, expanduser, join

from hdx.api.configuration import Configuration
from hdx.data.user import User
from hdx.facades.infer_arguments import facade
from hdx.utilities.dateparse import now_utc
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir_batch
from hdx.utilities.retriever import Retrieve

from hdx.scraper.hrp_projects.hrp_projects import HRPProjects

logger = logging.getLogger(__name__)

_USER_AGENT_LOOKUP = "hdx-scraper-hrp-projects"
_SAVED_DATA_DIR = "saved_data"  # Keep in repo to avoid deletion in /tmp
_UPDATED_BY_SCRIPT = "HDX Scraper: HRP Projects"


def main(
    save: bool = True,
    use_saved: bool = False,
) -> None:
    """Generate datasets and create them in HDX

    Args:
        save (bool): Save downloaded data. Defaults to True.
        use_saved (bool): Use saved data. Defaults to False.

    Returns:
        None
    """
    configuration = Configuration.read()
    if not User.check_current_user_organization_access(
        "ocha-hpc-tools", "create_dataset"
    ):
        raise PermissionError(
            "API Token does not give access to HPC Tools organisation!"
        )

    with temp_dir_batch(folder=_USER_AGENT_LOOKUP) as info:
        temp_dir = info["folder"]
        with Download() as downloader:
            retriever = Retrieve(
                downloader=downloader,
                fallback_dir=temp_dir,
                saved_dir=_SAVED_DATA_DIR,
                temp_dir=temp_dir,
                save=save,
                use_saved=use_saved,
            )
            hrp_projects = HRPProjects(configuration, retriever, temp_dir)
            now = now_utc()
            cutoff_year = now.year - 5
            countryiso3s = hrp_projects.get_data(cutoff_year)
            for countryiso3 in countryiso3s:
                dataset = hrp_projects.generate_dataset(countryiso3)
                if not dataset:
                    continue
                dataset.update_from_yaml(
                    path=join(dirname(__file__), "config", "hdx_dataset_static.yaml")
                )
                dataset.generate_quickcharts(
                    resource=0,
                    path=join(
                        dirname(__file__), "config", "hdx_resource_view_static.yaml"
                    ),
                )
                dataset.create_in_hdx(
                    remove_additional_resources=True,
                    match_resource_order=False,
                    hxl_update=False,
                    updated_by_script=_UPDATED_BY_SCRIPT,
                    batch=info["batch"],
                )

            logger.info("Finished processing!")


if __name__ == "__main__":
    facade(
        main,
        hdx_site="dev",
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
        project_config_yaml=join(
            dirname(__file__), "config", "project_configuration.yaml"
        ),
    )
