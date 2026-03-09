"""
ServScout - Service Inventory Scanner
Platform Team — Internal Developer Tooling
Version: 1.0.0
"""

import sys
import argparse
import json
from datetime import datetime, timezone

# import os
from pathlib import Path
from typing import Any
import yaml

REQUIRED_FIELDS = ["name", "team", "language", "version"]

def find_service_files(root_directory: str):
    """
    Recursively scan a directory and yield all service.yaml file paths.

    Args:
        root_directory: The root directory oath to scan.
    Yields:
        Path objects each pointing to each discovered service.yaml file
    Raises:
        NotADirectoryError: If root_dir is not a valid directory
    """
    root_directory_path = Path(root_directory)
    if root_directory_path.exists() and root_directory_path.is_dir():
        return (file for file in root_directory_path.rglob("service.yaml"))
    else:
        raise NotADirectoryError(
            "Not a valid directory, please check you root directory path"
        )


def parse_service_files(file: Path):
    """
    Reads and Parses the service.yaml file

    Args:
        file: path of the service file

    Returns:
        The parsed data from the YAML
    """
    with open(file, "r") as f:
        try:
            data = yaml.safe_load(f)
            return data
        except yaml.YAMLError as e:
            print("Error in the file", e)


def validate_services(data: dict[str, Any]):
    """
    Validates the given parsed data

    Args:
        data: dict[str, Any] - Dictionary with the parsed data from service.yaml

    Returns:
        tuple(status, missing_fileds)
        is_valid: bool - True or False based on the authenticity of the data
        missing_fields: list[] - List of the missing fields in the data if any, else empty list
    """
    is_valid = True

    if not data:
        is_valid = False
        return (is_valid, REQUIRED_FIELDS)

    missing_fields = [ key for key in REQUIRED_FIELDS if key not in data ]

    if missing_fields:
        is_valid = True
        return (is_valid, missing_fields)

    return (is_valid, missing_fields)


def build_report(services):
    """
    Build in memory services report for the discovered services

    Args:
        services: The filepaths of the services discovered
    Returns:
        report: A dict report of the discovered services with a summary
    """
    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {},
        "services": [],
    }

    for service_file in services:
        data = parse_service_files(service_file)
        is_valid, missing_fields = validate_services(data=data)

        report["summary"]["total_scanned"] = (
            report["summary"].get("total_scanned", 0) + 1
        )

        if is_valid:
            status = "valid"
            report["summary"]["total_valid"] = (
                report["summary"].get("total_valid", 0) + 1
            )
        else:
            status = "invalid"
            report["summary"]["total_with_errors"] = (
                report["summary"].get("total_with_errors", 0) + 1
            )

        errors = [f"Missing required field {field}" for field in missing_fields]

        report["services"].append(
            {
                "file": service_file.as_posix(),
                "status": status,
                "data": data,
                "errors": errors,
            }
        )

    return report


def write_report(report, output_path=Path(".")):
    """
    Writes the report to the disk

    Args:
        report: A dict report of the services
        output_path: The path where the output should be written, defaults to current working director
    """
    with open(output_path / "report.json", "w") as output_file:
        json.dump(report, output_file, indent=4)


# def traverse(path):
#     for basepath, directories, files in os.walk(path):
#         for file in files:
#             if file.endswith(".yaml"):
#                 yield os.path.join(basepath, file)


def main():

    parser = argparse.ArgumentParser(
        prog="servscout",
        description="ServScout — Scouts and inventories all services across the monorepo."
    )
    parser.add_argument(
        "path", 
        help="FilePath where the service files are present"
    )
    parser.add_argument(
        "--OUT", "-o",
        help="File path where the report file has to written to."
    )
    args = parser.parse_args()

    try:
        services = find_service_files(args.path)

    except NotADirectoryError as e:
        print(e)
        sys.exit(10001)

    report = build_report(services=services)
    write_report(report=report)

    print(report)


if __name__ == "__main__":
    main()
