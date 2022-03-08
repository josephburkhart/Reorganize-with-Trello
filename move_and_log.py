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
from distutils.dir_util import copy_tree
import shutil

# Functions
def shorten_path(full_path: Path, base_dir: Path):    #ref: https://stackoverflow.com/questions/53255659/from-pathlib-parts-tuple-to-string-path
    """Split the path into separate parts, select all elements after and including base_dir, and join them back together"""
    path_parts = full_path.parts
    base_index = path_parts.index(base_dir.name)
    return Path(*path_parts[base_index:])    # * expands the tuple into a flat comma separated params

def move(source: Path, destination: Path, base_dir: Path):
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
        print(f"{source.name} has been moved to" + str(shorten_path(destination.parent, base_dir)))
    
    # If name is a file, move it with shutil.move
    else:
        shutil.move(source, destination)
        print(f"{source.name} has been moved to " + str(shorten_path(destination.parent, base_dir)))
    return 0

def move_message(table_entry, destination: Path, base_dir: Path):
    '''Compose a message describing the movement
    Note that table_entry must have the following attributes: filepath'''
    source = table_entry.filepath
    short_source = shorten_path(source, base_dir)    #<--
    short_dest = shorten_path(destination, base_dir)    #<--
    move_msg = f"moved {table_entry.filepath.name} in {short_source.parent} to {short_dest.parent}\n"
    return move_msg

def error_message(table_entry, base_dir: Path):
    '''Compose a message describing the movement error
    Note that table_entry must have the following attributes: filepath, flag'''
    print(f"Issue found at {table_entry.filepath}") #better if this were a data structure
    
    # Determine the type of issue
    issues = {'d': 'Duplicate', 'u': 'Unclear'}
    issue_type = issues.get(table_entry.flag, 'Issue') #returns 'Issue' if flag is not 'd' or 'u'
    
    # Compose error message
    source = table_entry.filepath
    short_source_parent = str(shorten_path(source.parent, base_dir))    #<--
    error_msg = issue_type + ": " + str(table_entry.filepath.name) + " in " + short_source_parent #<--
    return error_msg

def log_message(log_file_path: Path, time, message):
    '''Write a timestamped message to a logfile'''
    with log_file_path.open(mode='a') as log_file:
            log_file.write(time + ' --- ' + message)