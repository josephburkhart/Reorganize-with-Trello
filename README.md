# Reorganize with Trello
Reorganize with Trello is a small python application for efficiently reorganizing large directory structures, particularly in asynchronous team projects. After linking a Trello account, board, and list to the application's configuration file, the user can sort items (both files and directories) into primary and secondary categories (i.e., directories and subdirectories) inside a new parent directory, and flag problematic items for review. Each time an item is flagged, the application will note the issue in a log file and create a trello card that specifies the type of problem, the path of the problematic item, and an optional card message. Each time an item is moved, the application will note the move in another log file.

## Requirements
- Python (3.7 or newer)
- [ruamel.yaml](https://yaml.readthedocs.io/en/latest/overview.html)


## Setup
1. Clone this repository, or simply download `move-and-log.py`, `trello.py`, `main.py`, and `config.yml` and place them together in a folder on your local machine.
2. In `config.yml`, set the configuration variables as follows:
   - `REORG_DIRECTORY`: full path to the new parent directory
   - `API_KEY`: Trello API Key linked to your Trello account (this can be obtained [here](https://trello.com/app-key/))
   - `OATH_TOKEN`: Trello authorization token linked to your Trello account (instructions can be found [here](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/))
   - `BOARD_NAME`: name of the board you want to create Trello cards in
   - `LIST_NAME`: name of the list you want to create Trello cards in
   - `MEMBER_NAMES`: usernames of the Trello board members that you want to tag on cards (make sure to replace all placeholder text before running the application)

## Usage
1. Using the command line, navigate to a directory in your original directory structure and run the application. The application will attempt to initialize and configure itself using the settings in `config.yml`. If the initialization is successful, the application will create a user interface as shown below.
   
<img src="https://github.com/josephburkhart/Reorganize-with-Trello/blob/8fe170749ee830f6f0c575d41d456c92e74bfbc7/images/Screenshot1.png" width="400">

2. In the application window, double click on a row to modify its values:
   - `name`: name of the file or directory in the current directory. This should not need to be modified.
   - `flag`: flag indicating whether an issue is present. `d` indicates item is a 'duplicate', `u` indicates item is 'unclear', and all other characters indicate a general 'issue'. These terms are used in the console output and the names of the trello cards.
   - `cat1` and `cat2`: primary and secondary categories that values will be used to determine the item's final destination: : `<REORG_DIRECTORY>/cat1/cat2`
   - `cat3`: optional third category inside `cat2`. If there is a value, it will be used to determine the item's final destination: : `<REORG_DIRECTORY>/cat1/cat2/cat3/`
   - `issue`: optional message describing the issue in detail. This message will be added to the description of the trello card.

3. Click the 'Process' button to process the table entries. Only entries with a flag or values for both `cat1` and `cat2` will be processed.

4. During processing, the application will generate two log files in the same directory as `main.py`: `change.log` logs all item movements, while `error.log` logs all item issues. If these files are already present, then the application will append new entries to them, rather than overwriting them.

## Additional Resources on Automating Trello with Python
1. https://www.timtreis.com/automatically-create-trello-cards-through-python-webscraping/
2. https://owlcation.com/stem/Automated-To-Do-Lists-Creating-Boards-Lists-And-Cards-Using-Python-And-The-Trello-API
