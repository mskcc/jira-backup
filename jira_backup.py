import requests
import argparse
from requests.adapters import HTTPAdapter
from getpass import getpass
from requests.packages.urllib3.util.retry import Retry
import urllib.parse
import os
import shutil
import logging
import json
import time
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("JIRA_BACKUP")


def get_request_backoff_session():
    session = requests.Session()
    retries = Retry(total=4, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])

    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_issues(start, batch, jira_board, jira_url, jira_username, jira_password):
    query_parameters = "/rest/api/2/search?jql=project={}&startAt={}&maxResults={}&fields=key&orderBy=key".format(
        jira_board, start, batch
    )
    query_url = urllib.parse.urljoin(jira_url, query_parameters)
    session = get_request_backoff_session()
    response = session.get(query_url, auth=(jira_username, jira_password))
    if not response.ok:
        print(
            "Error connecting to JIRA (status code: {}), please makse sure you credentials and url are correct".format(
                response.status_code
            )
        )
        exit(1)
    return response.json()


def get_single_issue(url, jira_username, jira_password):
    session = get_request_backoff_session()
    response = session.get(url, auth=(jira_username, jira_password))
    if not response.ok:
        print(
            "Error connecting to JIRA (status code: {}), please makse sure you credentials and url are correct".format(
                response.status_code
            )
        )
        exit(1)
    return response.json()


def download_attachment(filename, url, path, jira_username, jira_password):
    download_path = os.path.join(path, filename)
    with open(download_path, mode="wb") as file:
        session = get_request_backoff_session()
        response = session.get(url, stream=True, auth=(jira_username, jira_password))
        if not response.ok:
            print(
                "Error connecting to JIRA (status code: {}), please makse sure you credentials and url are correct".format(
                    response.status_code
                )
            )
            exit(1)
        for chunk in response.iter_content(chunk_size=10 * 1024):
            file.write(chunk)


def download_json(data, path):
    json_str = json.dumps(data, indent=4)
    json_path = os.path.join(path, "jira.json")
    with open(json_path, mode="w") as json_file:
        json_file.write(json_str)


def make_backup(status, request, jira_id, backup_dir, backup_dir_name):
    project_name = "{}_{}".format(request, jira_id)
    backup_path = os.path.join(backup_dir, backup_dir_name, status, project_name)
    if os.path.exists(backup_path):
        logger.info("Removing duplicate backup path: {}".format(str(backup_path)))
        shutil.rmtree(backup_path)
    os.makedirs(backup_path)
    return backup_path


def download_issue(
    issue_url, jira_username, jira_password, backup_dir, backup_dir_name
):
    issue_json = get_single_issue(issue_url, jira_username, jira_password)
    status = issue_json["fields"]["status"]["name"]
    request = issue_json["fields"]["summary"]
    jira_id = issue_json["key"]
    backup_path = make_backup(status, request, jira_id, backup_dir, backup_dir_name)
    download_json(issue_json, backup_path)
    for single_attachment in issue_json["fields"]["attachment"]:
        file_name = single_attachment["filename"]
        url = single_attachment["content"]
        download_attachment(file_name, url, backup_path, jira_username, jira_password)


def download_project(
    start,
    batch_size,
    jira_board,
    jira_url,
    jira_username,
    jira_password,
    sleep_time,
    backup_dir,
    backup_dir_name,
):
    current = start
    get_total = get_issues(0, 1, jira_board, jira_url, jira_username, jira_password)
    total = int(get_total["total"])
    self_list = {}
    while current < total:
        end = min(current + batch_size, total)
        logger.info(
            "Downloading tickets from {}, issues {} to {} out of {}".format(
                jira_board, current, end, total
            )
        )
        issues = get_issues(
            current,
            batch_size,
            jira_board,
            jira_url,
            jira_username,
            jira_password,
        )["issues"]
        for single_issue in issues:
            if single_issue["self"] in self_list:
                print("Duplicate of " + str(single_issue["self"]))
            self_list[single_issue["self"]] = 1
            download_issue(
                single_issue["self"],
                jira_username,
                jira_password,
                backup_dir,
                backup_dir_name,
            )
        current = current + batch_size
        time.sleep(sleep_time)


def compress_backup(backup_dir, backup_dir_name):
    backup_path = os.path.join(backup_dir, backup_dir_name)
    compressed_file = shutil.make_archive(
        base_name=backup_dir_name, format="gztar", root_dir=backup_path
    )


def main():
    backup_dir_default = os.getcwd()
    arg = argparse.ArgumentParser(
        description="Backup Jira issues and attachments",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg.add_argument(
        "--board", action="store", help="Name of jira board", default="RSL"
    )
    arg.add_argument(
        "--url",
        action="store",
        help="Url of JIRA",
        default="http://jira.mskcc.org:8090",
    )
    arg.add_argument(
        "--backupDir",
        action="store",
        help="Path to store the JIRA backup",
        default=backup_dir_default,
    )
    arg.add_argument(
        "--start",
        action="store",
        type=int,
        help="Issue number to backup (for continuing a previous backup)",
        default=0,
    )
    arg.add_argument(
        "--batchSize",
        action="store",
        type=int,
        help="Number of issues to backup at once",
        default=100,
    )
    arg.add_argument(
        "--sleepTime",
        action="store",
        type=int,
        help="Amount of time to sleep (seconds) in between batch requests",
        default=2,
    )

    parsed = arg.parse_args()
    jira_username = input("Enter your jira username:")
    jira_password = getpass("Enter your jira password:")

    backup_dir_name = "{}-backup".format(parsed.board)

    download_project(
        parsed.start,
        parsed.batchSize,
        parsed.board,
        parsed.url,
        jira_username,
        jira_password,
        parsed.sleepTime,
        parsed.backupDir,
        backup_dir_name,
    )
    compress_backup(parsed.backupDir, backup_dir_name)


if __name__ == "__main__":
    main()
