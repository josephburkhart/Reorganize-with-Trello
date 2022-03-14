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
import os
from distutils.dir_util import copy_tree
import shutil

# Functions
def shorten_path(full_path: Path, base_dir: Path):    #ref: https://stackoverflow.com/questions/53255659/from-pathlib-parts-tuple-to-string-path
    """Split the path into separate parts, select all elements after and including base_dir, and join them back together"""
    path_parts = full_path.parts
    base_index = path_parts.index(base_dir.name)
    return Path(*path_parts[base_index:])    # * expands the tuple into a flat comma separated params

def move(source: Path, destination: Path, base_dir: Path, sep: str):
    '''Moves specified item at source path to destination path,
    printing messages to the console as needed.
    sep is the path delimiter that will be used in console output'''
    s = sep
    if source.is_dir():
        name = f"{s}{source.name}{s}"
    else:
        name = f"{source.name}"
    print(f"Attempting to move {source.name}...")

    # Check if the named file/directory exists
    if not source.exists():
        print(f"Warning: {name} does not exist in {source.parent}{s}\nMove has been skipped. Continuing...\n")
        return
    
    # Check if there is a duplicate file/directory at the destination
    if destination.exists():
        print(f"Warning: {name} already exists in {destination.parent}{s}\nMove has been skipped. Continuing...\n")
        return
    
    # Create destination folder if necessary    TODO: modify print statement to include base reorg directory
    if not destination.parent.exists():
        print(f"Warning: destination does not exist: .{s}{shorten_path(destination.parent, base_dir)}{s}\nCreating destination... ", end="")
        destination.parent.mkdir(parents=True, exist_ok=False) #all intermediate folders are also created
        print("Done")
    
    # If name is a directory, move it with copy_tree 
    if source.is_dir():
        #destination.mkdir(parents=False, exist_ok=False)    
        copy_tree(str(source), str(destination), preserve_times=True)
        shutil.rmtree(source)
    
    # If name is a file, move it with shutil.move
    else:
        shutil.move(source, destination)

    print(f"{name} has been moved to .{s}{shorten_path(destination.parent, base_dir)}{s}\n")
    return 0

def move_message(source: Path, destination: Path, base_dir: Path, sep: str):
    '''Compose a message describing the movement
    Note that table_entry must have the following attributes: name
    sep is the path delimiter that will be used in the returned message'''
    s = sep
    if source.is_dir():
        name = f"{s}{source.name}{s}"
    else:
        name = f"{source.name}"
    move_msg = f"moved {name} in {source.parent}{s} to {destination.parent}{s}\n"
    return move_msg

def error_message(table_entry, source: Path, base_dir: Path, short_paths: bool, sep: str):
    '''Compose a message describing the movement error
    If short_paths=True, then the source path will be shortened to base_dir
    Note that table_entry must have the following attributes: name, flag
    sep is the path delimiter that will be used in the returned message'''
    s = sep

    # Determine the type of issue
    issues = {'d': 'Duplicate', 'u': 'Unclear'}
    issue_type = issues.get(table_entry.flag, 'Issue') #returns 'Issue' if flag is not 'd' or 'u'
    
    # Compose error message
    if source.is_dir():
        name = f"{s}{table_entry.name}{s}"
    else:
        name = source.name
    
    if short_paths:
        source = shorten_path(source, base_dir)
        error_msg = f"{issue_type}: {name} in .{s}{source.parent}{s}"
    else:
        error_msg = f"{issue_type}: {name} in {source.parent}{s}"
    return error_msg

def log_message(log_file_path: Path, time, message):
    '''Write a timestamped message to a logfile'''
    with log_file_path.open(mode='a') as log_file:
            log_file.write(time + ' --- ' + message)