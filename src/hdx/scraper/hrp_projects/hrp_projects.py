#!/usr/bin/python
"""hrp projects scraper"""

import logging
from typing import List, Optional

from hdx.api.configuration import Configuration
from hdx.api.utilities.hdx_error_handler import HDXErrorHandler
from hdx.data.dataset import Dataset
from hdx.location.country import Country
from hdx.utilities.dateparse import parse_date
from hdx.utilities.dictandlist import dict_of_lists_add, dict_of_sets_add
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)


class HRPProjects:
    def __init__(
        self,
        configuration: Configuration,
        retriever: Retrieve,
        error_handler: HDXErrorHandler,
        temp_dir: str,
    ):
        self._configuration = configuration
        self._retriever = retriever
        self._error_handler = error_handler
        self._temp_dir = temp_dir
        self.plans_data_json = {}
        self.plans_data_csv = {}
        self.dates = {}
        self.hrp_countries = []
        self.gho_countries = []

    def get_data(self, current_year: int, cutoff_year: int) -> List[str]:
        plans_data = self._retriever.download_json(self._configuration["plans_url"])
        for plan in plans_data["data"]:
            plan_code = plan["planVersion"]["code"]

            # skip if there's no country ISO3
            iso3s = []
            for location in plan["locations"]:
                if location.get("adminLevel") == 0:
                    iso3 = location.get("iso3")
                    if iso3:
                        iso3s.append(iso3)
            if len(iso3s) == 0:
                logger.info(f"Skipping {plan_code} (no country code)")
                continue

            # skip if it's from before the cutoff year
            plan_year = 0
            for year in plan["years"]:
                if "year" in year and int(year["year"]) >= plan_year:
                    plan_year = int(year["year"])
            if plan_year < cutoff_year:
                logger.info(f"Skipping {plan_code} (before {cutoff_year})")
                continue

            # update HRP and GHO lists
            if plan_year == current_year:
                if (
                    plan["planVersion"]["subtitle"].lower()
                    in self._configuration["hrp_subtitles"]
                ):
                    for iso3 in iso3s:
                        self.hrp_countries.append(iso3)
                if plan["planVersion"]["isPartOfGHO"]:
                    for iso3 in iso3s:
                        self.gho_countries.append(iso3)

            # skip if it doesn't have any projects
            project_url = self._configuration["api_pattern"].format(
                code=plan_code, rows=500
            )
            project_data_json = self._retriever.download_json(project_url)
            if len(project_data_json["data"]["results"]) == 0:
                logger.info(f"Skipping {plan_code} (no projects)")
                continue

            # add these plans and dates
            start_date = parse_date(plan["planVersion"].get("startDate"))
            end_date = parse_date(plan["planVersion"].get("endDate"))

            plan_row = {
                "code": plan_code,
                "name": plan["planVersion"].get("name"),
                "start": plan["planVersion"].get("startDate"),
                "end": plan["planVersion"].get("endDate"),
                "url": self._configuration["api_pattern"].format(
                    code=plan_code, rows=100000
                ),
            }
            for iso3 in iso3s:
                dict_of_sets_add(self.dates, iso3, start_date)
                dict_of_sets_add(self.dates, iso3, end_date)
                dict_of_lists_add(self.plans_data_json, iso3, plan_row)

            # paginate through results
            project_data = project_data_json["data"]["results"]
            pages = project_data_json["data"]["pagination"]["pages"]
            if pages > 1:
                for i in range(2, pages + 1):
                    extra_project_data = self._retriever.download_json(
                        project_url + f"&page={i}"
                    )
                    project_data.extend(extra_project_data["data"]["results"])
            for row in project_data:
                csv_row = {
                    key: value
                    for key, value in row.items()
                    if key in self._configuration["hxl_tags"]
                }
                if row["locations"] is not None:
                    csv_row["locations"] = ", ".join(
                        [
                            country["iso3"]
                            for country in row["locations"]
                            if country["iso3"]
                        ]
                    )
                if row["globalClusters"] is not None:
                    csv_row["globalClusters"] = ", ".join(
                        [cluster["name"] for cluster in row["globalClusters"]]
                    )
                if row["organizations"] is not None:
                    csv_row["organizations"] = ", ".join(
                        [org["name"] for org in row["organizations"]]
                    )
                if row["plans"] is not None:
                    plan_names = list(set([plan["name"] for plan in row["plans"]]))
                    csv_row["plans"] = ", ".join(plan_names)
                csv_row["Response plan code"] = plan_code
                for iso3 in iso3s:
                    if iso3 not in self.plans_data_csv:
                        self.plans_data_csv[iso3] = {}
                    dict_of_lists_add(self.plans_data_csv[iso3], plan_code, csv_row)

        return sorted(list(self.plans_data_json.keys()))

    def check_hrp_gho(self, current_year: int, flag=True) -> List:
        country_data = Country.countriesdata()["countries"]
        edits = []
        for data_type in ["GHO", "HRP"]:
            exceptions = self._configuration["hrp_gho_exceptions"].get(
                f"{data_type}_{current_year}", {}
            )
            add_countries = exceptions.get("add", [])
            remove_countries = exceptions.get("remove", [])
            old_list = [
                key
                for key in country_data
                if country_data[key][f"#indicator+bool+{data_type.lower()}"] == "Y"
            ]
            new_list = self.gho_countries if data_type == "GHO" else self.hrp_countries
            new_list = new_list + add_countries
            new_list = [iso for iso in new_list if iso not in remove_countries]
            new_list = list(set(new_list))
            if sorted(old_list) != sorted(new_list):
                add_countries = [c for c in new_list if c not in old_list]
                edits.append(add_countries)
                remove_countries = [c for c in old_list if c not in new_list]
                edits.append(remove_countries)
                if flag and len(add_countries) > 0:
                    self._error_handler.add_message(
                        "HRP Projects",
                        data_type,
                        f"Add {', '.join(add_countries)} to country list",
                    )
                if flag and len(remove_countries) > 0:
                    self._error_handler.add_message(
                        "HRP Projects",
                        data_type,
                        f"Remove {', '.join(remove_countries)} from country list",
                    )
        return edits

    def generate_dataset(self, countryiso3: str) -> Optional[Dataset]:
        country_name = Country.get_country_name_from_iso3(countryiso3)
        if not country_name:
            logger.error(f"Could not find iso {countryiso3}")
            return None
        dataset = Dataset(
            {
                "name": f"hrp-projects-{countryiso3.lower()}",
                "title": f"{country_name}: Response Plan projects",
            }
        )
        start_date = min(self.dates[countryiso3])
        end_date = max(self.dates[countryiso3])
        dataset.set_time_period(start_date, end_date)
        dataset.add_tags(self._configuration["tags"])
        dataset.add_country_location(countryiso3)
        dataset["caveats"] = (
            f"1. Includes only projects registered as part of the Humanitarian Programme Cycle.\r\n2. Some projects are excluded for protection or personal-privacy reasons.\r\n3. For multi-country response plans, _all_ projects are included, and some might not apply to {country_name}."
        )
        dataset["notes"] = (
            f"Projects proposed, in progress, or completed as part of the annual {country_name} Humanitarian Response Plans (HRPs) or other Humanitarian Programme Cycle plans. The original data is available on https://hpc.tools\r\n\r\n**Important:** some projects in {country_name} might be missing, and others might not apply specifically to {country_name}. See _Caveats_ under the _Additional information_ tab."
        )

        # Add two resources (HXL and JSON) for each plan specified
        hxl_tags = self._configuration["hxl_tags"]
        headers = list(hxl_tags.keys())
        plans = self.plans_data_json[countryiso3]
        for plan in sorted(plans, key=lambda plan: plan["start"], reverse=True):
            plan_code = plan["code"]
            plan_name = plan["name"]
            data_csv = self.plans_data_csv[countryiso3][plan_code]
            resourcedata_csv = {
                "name": f"{plan_code.lower()}-{countryiso3.lower()}-projects.csv",
                "description": f"Projects for {plan_name}: simplified CSV data, with HXL hashtags.",
            }
            dataset.generate_resource_from_iterable(
                headers,
                data_csv,
                hxl_tags,
                self._temp_dir,
                f"{plan_code.lower()}-{countryiso3.lower()}-projects.csv",
                resourcedata_csv,
                encoding="utf-8-sig",
            )

            resourcedata_json = {
                "name": f"{plan_code.lower()}-{countryiso3.lower()}-projects.json",
                "description": f"Projects for {plan_name}: original JSON, from HPC.tools",
                "url": plan["url"],
                "format": "json",
            }
            dataset.add_update_resource(resourcedata_json)

        return dataset
