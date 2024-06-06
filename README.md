# Jira Backup

Use this script to backup your boards on JIRA. This includes all the comments/metadata as well as all the attachments.
While jira provides its own backup facility, the object of this script is to create a readable backup that is parseable without JIRA.

# Quick start

### Setup the python virtual env

```
python3 -m venv venv
source venv/bin/activate
```

### Install the required packages

```
pip3 install -r requirements.txt
```

Backup your board

```
python3 jira_backup.py --board [YOUR_BOARD_NAME]
```

> [!NOTE]
> This is using the defualt parameters for the url and backup storage, if you want to add further configuration please read the running section of the doc

`jira_backup` will ask for your jira credentials and then it will download and compress your backup

# Running the script

The parameters of the script are as follows:

```
usage: jira_backup.py [-h] [--board BOARD] [--url URL] [--backupDir BACKUPDIR]
                      [--start START] [--batchSize BATCHSIZE] [--sleepTime SLEEPTIME]

Backup Jira issues and attachments

options:
  -h, --help            show this help message and exit
  --board BOARD         Name of jira board (default: RSL)
  --url URL             Url of JIRA (default: http://jira.mskcc.org:8090)
  --backupDir BACKUPDIR
                        Path to store the JIRA backup (default: /Users/nkumar/work/jira-
                        backup)
  --start START         Issue number to backup (for continuing a previous backup) (default:
                        0)
  --batchSize BATCHSIZE
                        Number of issues to backup at once (default: 100)
  --sleepTime SLEEPTIME
                        Amount of time to sleep (seconds) in between batch requests
                        (default: 2)
```

`sleepTime` and `batchSize` are important so we don't overload the jira server.
Use `start` if you want to resume a backup

# Backup structure

The structure of the backup is organized by [Status]/[Ticket_name]\_[JIRA_ID]
Within each of those folders there is a `jira.json` that contains all the jira metadata including comments made on the ticket, as well as a list of all the attachments downloaded to the folder.

## Example backup structure

This is an example backup structure for a roslin project

```
08390_B_RSL-429
├── Proj_08390_B_QC_Report.pdf
├── Proj_08390_B_delivery_email.txt
├── Proj_08390_B_request.txt
├── Proj_08390_B_sample_data_clinical.txt
├── Proj_08390_B_sample_grouping.txt
├── Proj_08390_B_sample_mapping.txt
├── Proj_08390_B_sample_pairing.txt
└── jira.json
```
