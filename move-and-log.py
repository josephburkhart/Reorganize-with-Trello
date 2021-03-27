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
import sys
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

# Handle Command Line Arguments
num_args = 3        #expected number of arguments
#args = sys.argv[1:]   #preserve the list of arguments in a non-global object
args = ["files4.txt", "Conventional", "Daily-Journaling"]
if len(args) != num_args:
    raise SystemExit(f"Usage: {sys.argv[0]} requires {num_args} arguments") 

# Configuration
credentials_path = Path.cwd() / 'trello-key-and-token.txt'  #text file with api key and oath token for bot's Trello account
credentials = credentials_path.read_text().split(',')

API_KEY = credentials[1]
OATH_TOKEN = credentials[3]
BOARD_NAME = "KAD-Reorganize"
LIST_NAME= "Issues"
USER_NAMES = ["Admin Username 1", "Username 2", "etc"]

files_path = Path.cwd() / args[0]   #text file that lists the full paths to each file I want to move

errors_log_path = Path.cwd() / 'errors.log'
changes_log_path = Path.cwd() / 'changes.log'

base_dir = Path.cwd()          #used to shorten paths later - TODO: change this to an absolute path

data_stream = args[1]    #first organizational tier
data_type = args[2]      #second organizational tier

# Path Data
paths = files_path.read_text().splitlines()     #names of files to move - TODO: remove blank lines
paths = [Path(p) for p in paths]            #turn strings into path objects

#Find trello ids
board_id = trello.find_board(BOARD_NAME)
list_id = trello.find_list(board_id, LIST_NAME)
member_ids = trello.find_members(USER_NAMES)

# Move the files and write to log
for p in paths:
    #get currrent time (used in log messages)
    current_time = time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(time.time()))
    
    #paths for movement
    name = str(p.name)
    source = p         
    destination = base_dir / '2015_reorg' / data_stream / data_type / name
    
    #check for error flag
    if "!" in name[-2:]:
        print(f"Issue found at {name[:name.index('!')]}")
        
        #Determine the type of issue
        if name[-1] == "d":
            issue_type = "Duplicate"
            
        elif name[-1] == "u":
            issue_type = "Unclear"
            
        else:
            issue_type = "Issue"
        
        #make an issue card
        card_name = issue_type + ": " + name[:name.index('!')] + " in " + str(shorten_path(source.parent, base_dir))
        card_description = ""
        trello.create_card(list_id, card_name, card_description, member_ids) #TODO: make card_description an optional argument
        
        #log the error
        error_msg = current_time + " --- " + card_name + "\n"
        with errors_log_path.open(mode='a') as log_file:
            log_file.write(error_msg)
        continue
    
    #check if the named file/directory exists
    if not p.exists():
        print(f"Warning: {name} does not exist in {source.parent}. Move has been skipped. Continuing...")
        continue
    
    #check if there is a duplicate file/directory at the destination
    if destination.exists():
        print("Warning: f{name} already exists in {destination.parent}! Move has been skipped. Continuing...")
        continue
    
    #create destination folder if necessary
    if not destination.parent.exists():
        print(f"Destination does not exist: {destination.parent.parent.name}/{destination.parent.name} \nCreating destination...", end="")
        destination.parent.mkdir(parents=True, exist_ok=False) #all intermediate folders are also created
        print("Done\n")
    
    #if name is a directory, move it with copy_tree 
    if source.is_dir():
        #destination.mkdir(parents=False, exist_ok=False)    
        copy_tree(str(source), str(destination), preserve_times=True)
        shutil.rmtree(source)
        print(f"{name} has been moved")
    
    #if name is a file, move it with shutil.move
    else:
        shutil.move(source, destination)
        print(f"{name} has been moved")
        
    #log the move
    changes_msg = current_time + " --- moved " + name + " in " + str(shorten_path(source.parent, base_dir)) + " to " + str(shorten_path(destination.parent, base_dir)) + "\n"
    with changes_log_path.open(mode='a') as log_file:
        log_file.write(changes_msg)
    
