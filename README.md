# HStudio

## Authorization

### Github
- Repository: https://github.com/gourmets/experiments
- Every project has a folder in the repo.
- Repository accesses are already granted.
- Get personal access token: [Creating a personal access token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token)

### Google Sheet
- Every project has a sheet.
- Sheet accesses are shared.
- Get `credentials.json`: [Python Quickstart Step 1: Turn on the Google Sheets API](https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the)

## Design

### Components

- 1 Repo

    Github repository for code and log

- 1 Sheet

    Google Sheet for hyperparameters and results

- N Worker

    Google Colab for training

### User Workflow
1. Add a row in Sheet
2. Push code to Repo
3. Mark row status as ready
4. 

### Worker Workflow

1. Worker fetch pending task (code) from Sheet
2. Worker complete training
3. Worker push result to Sheet, log to Repo
4. Repeat from 1