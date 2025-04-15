#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""

import logging
from copy import deepcopy
from os.path import dirname, expanduser, join

from hdx.api.configuration import Configuration
from hdx.api.utilities.hdx_error_handler import HDXErrorHandler
from hdx.data.user import User
from hdx.facades.infer_arguments import facade
from hdx.utilities.dateparse import now_utc
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir_batch
from hdx.utilities.retriever import Retrieve
from hdx.utilities.state import State

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
    with HDXErrorHandler(should_exit_on_error=True) as error_handler:
        with State(
            "update_dates.txt",
            State.dates_str_to_country_date_dict,
            State.country_date_dict_to_dates_str,
        ) as state:
            state_dict = deepcopy(state.get())
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
                    hrp_projects = HRPProjects(
                        configuration, retriever, error_handler, temp_dir
                    )
                    now = now_utc()
                    hrp_projects.get_data(
                        current_year=now.year, cutoff_year=now.year - 5
                    )
                    hrp_projects.check_hrp_gho()
                    countryiso3s = hrp_projects.check_state(state_dict)
                    for countryiso3 in countryiso3s:
                        dataset = hrp_projects.generate_dataset(countryiso3)
                        if not dataset:
                            continue
                        dataset.update_from_yaml(
                            path=join(
                                dirname(__file__), "config", "hdx_dataset_static.yaml"
                            )
                        )
                        dataset.generate_quickcharts(
                            resource=0,
                            path=join(
                                dirname(__file__),
                                "config",
                                "hdx_resource_view_static.yaml",
                            ),
                        )
                        dataset.create_in_hdx(
                            remove_additional_resources=True,
                            match_resource_order=False,
                            hxl_update=False,
                            updated_by_script=_UPDATED_BY_SCRIPT,
                            batch=info["batch"],
                        )

                    state.set(state_dict)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
        project_config_yaml=join(
            dirname(__file__), "config", "project_configuration.yaml"
        ),
    )
