# Reorganize with Trello
Tools for efficiently reorganizing large directory structures using Python and Trello’s REST API. Files and directories are moved to a new, adjacent directory `2015_reorg/{cat1}/{cat2}`, where `cat1` is the a category under the new organizational scheme and `cat2` is a subcategory of `cat1`. Files are moved unless they are flagged with an issue, in which case a Trello card is created with the path of the offending file/directory and specified members of the Trello board are tagged on the card.

## Requirements
- Python (3.7 or newer)

## Setup
Download `move-and-log.py`, `trello-key-and-token.txt`, `changes.log`, `errors.log`, and place them in the top-level directory of the directory structure you wish to reorganize

## Usage
1. Request a Trello API Key and Authorization Token (see instructions [here](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/))
2. In `trello-key-and-token.txt`, change `your_key_here` to your API key. Then change `your_token_here` to your token.
3. In `move-and-log.py`, change the configuration variables as follows:
    - set `BOARD_NAME` to the name of the board on which you want to make Trello cards
    - set `LIST_NAME` to the name of the list in which you want to make cards
    - set `USER_NAMES` to the usernames of the people you want to tag on the cards that are made with `move-and-log.py`
4. Open a terminal session and navigate to the directory containing `move-and-log.py`
5. For a given `cat1` and `cat2` (see first section above):
      1. Navigate to a directory containing some directories or files that you wish to move to a specific category and subcategory
      2. Enter the command `dir /s /b > files.txt` (this is windows cmd syntax, adapt to your OS as appropriate)
      3. In `files.txt`, remove all paths corresponding to files and directories that you do not want to move
      4. In `files.txt`, add `!u`, `!d`, or `!` to paths of files/directories that are unclear (e.g., contents unknown or poorly documented), duplicates, or otherwise problematic, respectively
      5. Move `files.txt` to the directory containing `move-and-log.py`
      6. In the terminal, enter the command `python move-and-log.py cat1 cat2` (but in place of `cat1` and `cat2` enter your own categories)
6. Repeat step 5 as necessary

## Additional Resources on Automating Trello with Python
1. https://www.timtreis.com/automatically-create-trello-cards-through-python-webscraping/
2. https://owlcation.com/stem/Automated-To-Do-Lists-Creating-Boards-Lists-And-Cards-Using-Python-And-The-Trello-API
