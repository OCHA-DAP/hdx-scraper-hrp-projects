from os.path import join

import pytest
from hdx.api.configuration import Configuration
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve
from hdx.utilities.useragent import UserAgent


class TestHRPProjects:
    def test_hrp_projects(self, configuration, fixtures_dir, input_dir, config_dir):
        with temp_dir(
            "test_hrp_projects",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader=downloader,
                    fallback_dir=tempdir,
                    saved_dir=input_dir,
                    temp_dir=tempdir,
                    save=False,
                    use_saved=True,
                )

                dataset.update_from_yaml(
                    path=join(config_dir, "hdx_dataset_static.yaml")
                )
