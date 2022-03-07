# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 15:41:09 2021

@author: Joseph

This script takes as input a txt file containing a list of file paths and two
categories data-stream and data-type, and moves the named files to new directories with the 
names of the input categories.

In order to work, the following must be in the cwd:
- files.txt
- files named in files.txt
- directory '2015_reorg'

      
"""
from pathlib import Path
import requests
from collections import namedtuple
from distutils.dir_util import copy_tree
import shutil
import time 
import trello

# Functions
def shorten_path(full_path, base_dir: str):    #ref: https://stackoverflow.com/questions/53255659/from-pathlib-parts-tuple-to-string-path
    """Split the path into separate parts, select all elements after and including base_dir, and join them back together"""
    path_parts = full_path.parts
    base_index = path_parts.index(base_dir.name)
    return Path(*path_parts[base_index:])    # * expands the tuple into a flat comma separated params

def move(source: Path, destination: Path):
    '''Moves specified item at source path to destination path,
    printing messages to the console as needed'''
    # Check if the named file/directory exists
    if not source.exists():
        print(f"Warning: {source.name} does not exist in {source.parent}\nMove has been skipped. Continuing...")
        return
    
    # Check if there is a duplicate file/directory at the destination
    if destination.exists():
        print("Warning: f{source.name} already exists in {destination.parent}!\nMove has been skipped. Continuing...")
        return
    
    # Create destination folder if necessary
    if not destination.parent.exists():
        print(f"Destination does not exist: {destination.parent.parent.name}\\{destination.parent.name} \nCreating destination...", end="")
        destination.parent.mkdir(parents=True, exist_ok=False) #all intermediate folders are also created
        print("Done\n")
    
    # If name is a directory, move it with copy_tree 
    if source.is_dir():
        #destination.mkdir(parents=False, exist_ok=False)    
        copy_tree(str(source), str(destination), preserve_times=True)
        shutil.rmtree(source)
        print(f"{name} has been moved to" + str(shorten_path(destination.parent, base_dir)))
    
    # If name is a file, move it with shutil.move
    else:
        shutil.move(source, destination)
        print(f"{name} has been moved to " + str(shorten_path(destination.parent, base_dir)))
    return 0

def move_message(table_entry):
    '''Compose a message describing the movement'''
    name = table_entry.filepath.name
    short_source_parent = str(shorten_path(source.parent, base_dir))    #<--
    short_dest_parent = str(shorten_path(destination.parent, base_dir))    #<--
    move_msg = f"moved {table_entry.filepath.name} in {short_source_parent} to {short_dest_parent}\n"
    return move_msg

def error_message(table_entry):
    '''Compose a message describing the movement error'''
    print(f"Issue found at {table_entry.filepath}") #better if this were a data structure
    
    # Determine the type of issue
    issues = {'d': 'Duplicate', 'u': 'Unclear'}
    issue_type = issues.get(table_entry.flag, 'Issue') #returns 'Issue' if flag is not 'd' or 'u'
    
    # Compose error message
    error_msg = issue_type + ": " + table_entry.filepath + " in " + str(shorten_path(source.parent, base_dir)) #<--
    return error_msg

def log_message(log_file_path, time, message):
    '''Write a timestamped message to a logfile'''
    with log_file_path.open(mode='a') as log_file:
            log_file.write(time + ' --- ' + message)

# Configuration
credentials_path = Path.cwd() / 'trello-key-and-token-test.txt'  #text file with api key and oath token for bot's Trello account
credentials = credentials_path.read_text().split(',')

API_KEY = credentials[1]
OATH_TOKEN = credentials[3]
BOARD_NAME = "KAD-Reorganize"
LIST_NAME= "Issues"
#USER_NAMES = ["kevinfisher6", "sheripak"]
USER_NAMES = ["joseph80236002"]


files_path = Path.cwd() / args[0]   #text file that lists the full paths to each file I want to move

errors_log_path = Path.cwd() / 'errors.log'
changes_log_path = Path.cwd() / 'changes.log'

base_dir = Path.cwd()           #used to shorten paths later - TODO: change this to an absolute path
reorg_dir = Path.cwd() / 'testdirectory2'   #this needs to be configured by each user

data_stream = args[1]    #first organizational tier
data_type = args[2]      #second organizational tier

# Path Data
paths = files_path.read_text().splitlines()     #names of files to move - TODO: remove blank lines
paths = [Path(p) for p in paths]            #turn strings into path objects

# Compose data structure
TableEntry = namedtuple("TableEntry", 'filepath flag cat1 cat2 cat3 issue')
tableentries = (TableEntry(p, '', data_stream, data_type, '', '') for p in paths)

#Find trello ids
board_id = trello.find_board(BOARD_NAME, API_KEY, OATH_TOKEN)
list_id = trello.find_list(board_id, LIST_NAME, API_KEY, OATH_TOKEN)
member_ids = trello.find_members(USER_NAMES, API_KEY, OATH_TOKEN)

# Move the files and write to log
for e in tableentries:
    #get currrent time (used in log messages)
    current_time = time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(time.time()))
    
    #paths for movement
    name = str(e.filepath.name)
    source = e.filepath         
    destination = base_dir / reorg_dir / e.cat1 / e.cat2 / name
    
    if e.flag == '':
        # Move and log
        move(source=e.filepath, destination=destination) #need to make exception for when cat3 does not exist
        msg = move_message(table_entry=e)
        log_message(log_file_path=changes_log_path, time=current_time, message=msg)

    else:
        # Log the error
        msg = error_message(table_entry=e)
        log_message(log_file_path=errors_log_path, time=current_time, message=msg)

        # Make an issue card
        card_name = error_message   # TODO: need shorten_dir here?
        card_description = ""
        trello.create_card(list_id, card_name, card_description, member_ids, API_KEY, OATH_TOKEN) #TODO: make card_description an optional argument
    
