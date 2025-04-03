from os.path import join

from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.hrp_projects.hrp_projects import HRPProjects


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
                hrp_projects = HRPProjects(configuration, retriever, tempdir)
                countryiso3s = hrp_projects.get_data(2018)
                assert countryiso3s == ["IRQ"]
                dataset = hrp_projects.generate_dataset("IRQ")
                dataset.update_from_yaml(
                    path=join(config_dir, "hdx_dataset_static.yaml")
                )
                dataset.generate_quickcharts(
                    resource=0,
                    path=join(config_dir, "hdx_resource_view_static.yaml"),
                )

                assert dataset == {
                    "name": "hrp-projects-irq",
                    "title": "Iraq: Response Plan projects",
                    "dataset_date": "[2022-01-01T00:00:00 TO 2022-12-31T23:59:59]",
                    "tags": [
                        {
                            "name": "humanitarian response plan-hrp",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        },
                        {
                            "name": "hxl",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        },
                        {
                            "name": "who is doing what and where-3w-4w-5w",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        },
                    ],
                    "groups": [{"name": "irq"}],
                    "caveats": "1. Includes only projects registered as part of the Humanitarian "
                    "Programme Cycle.\r\n2. Some projects are excluded for protection or personal-"
                    "privacy reasons.\r\n3. For multi-country response plans, _all_ projects are "
                    "included, and some might not apply to Iraq.",
                    "notes": "Projects proposed, in progress, or completed as part of the annual "
                    "Iraq Humanitarian Response Plans (HRPs) or other Humanitarian Programme Cycle "
                    "plans. The original data is available on https://hpc.tools\r\n\r\n**Important:** "
                    "some projects in Iraq might be missing, and others might not apply specifically "
                    "to Iraq. See _Caveats_ under the _Additional information_ tab.",
                    "license_id": "cc-by-igo",
                    "methodology": "Registry",
                    "dataset_source": "HPC Tools",
                    "package_creator": "HDX Data Systems Team",
                    "private": False,
                    "maintainer": "1a1776f4-d825-4c62-b809-e9127278763d",
                    "owner_org": "ocha-hpc-tools",
                    "data_update_frequency": -2,
                    "subnational": "0",
                    "dataset_preview": "resource_id",
                }

                resources = dataset.get_resources()
                assert len(resources) == 2
                assert resources[0] == {
                    "name": "rsyr22-irq-projects.csv",
                    "description": "Projects for Syrian Arab Republic Regional Refugee and "
                    "Resilience Plan (3RP) 2022 (sector): simplified CSV data, with HXL hashtags.",
                    "format": "csv",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                    "dataset_preview_enabled": "True",
                }
                assert resources[1] == {
                    "name": "rsyr22-irq-projects.json",
                    "description": "Projects for Syrian Arab Republic Regional Refugee and "
                    "Resilience Plan (3RP) 2022 (sector): original JSON, from HPC.tools",
                    "url": "https://api.hpc.tools/v2/public/project/search?planCodes=RSYR22&"
                    "excludeFields=locations,governingEntities,targets&limit=100000",
                    "format": "json",
                    "resource_type": "api",
                    "url_type": "api",
                    "dataset_preview_enabled": "False",
                }
                assert_files_same(
                    join(fixtures_dir, "rsyr22-irq-projects.csv"),
                    join(tempdir, "rsyr22-irq-projects.csv"),
                )
