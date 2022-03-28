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
def shorten_path(full_path: Path, shorten_index: int):    #ref: https://stackoverflow.com/questions/53255659/from-pathlib-parts-tuple-to-string-path
    """Split the path into separate parts, select all elements after and including base_dir, and join them back together"""
    path_parts = full_path.parts
    base_index = path_parts.index(base_dir.name)
    return Path(*path_parts[base_index:])    # * expands the tuple into a flat comma separated params

def path_from_common_parent(mainpath: Path, comparepath: Path, parent_index: int):
    """Takes a main and a comparison path, makes an ordered list of their common 
    parents, selects the common parent specified by parent_index, and returns
    a new path from the selected parent to the end of the main path.
    
    Note: raises ValueError if parent_index is out of range"""
    parts_in_common = []
    for part in mainpath.parts:
        if part in comparepath.parts:
            if mainpath.parts.index(part) == comparepath.parts.index(part):
                parts_in_common.append(part)
        else:
            break
    
    base_part = parts_in_common[parent_index]
    base_index = mainpath.parts.index(base_part)
    return Path(*mainpath.parts[base_index:])

def move(source: Path, destination: Path, shorten_index: int, sep: str):
    """Moves specified item at source path to destination path,
    printing messages to the console as needed.
    sep is the path delimiter that will be used in console output"""
    s = sep
    if source.is_dir():
        name = f"{s}{source.name}{s}"
    else:
        name = f"{source.name}"

    # Create shortened paths
    try:
        source_parent_for_print = f"{s}{path_from_common_parent(source.parent, destination, shorten_index)}{s}"
        dest_parent_for_print = f"{s}{path_from_common_parent(destination.parent, source, shorten_index)}{s}"
    except IndexError:
        source_parent_for_print = f"{source.parent}{s}"
        dest_parent_for_print = f"{destination.parent}{s}"

    # Check if the named file/directory exists
    if not source.exists():
        print(f"Warning: {name} does not exist in {source_parent_for_print}")
        raise MoveError('Source does not exist')
    
    # Check if there is a duplicate file/directory at the destination
    if destination.exists():
        print(f"Warning: {name} already exists in {dest_parent_for_print}")
        raise MoveError('Source duplicated at destination')
    
    # Create destination folder if necessary    TODO: modify print statement to include base reorg directory
    if not destination.parent.exists():
        print(f"Warning: destination does not exist: {dest_parent_for_print}\nCreating destination... ", end="")
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

    print(f"{name} has been moved to {dest_parent_for_print}\n")

def move_message(source: Path, destination: Path, sep: str):
    """Compose a message describing the movement
    Note that table_entry must have the following attributes: name
    sep is the path delimiter that will be used in the returned message"""
    s = sep
    if source.is_dir():
        name = f"{s}{source.name}{s}"
    else:
        name = f"{source.name}"
    move_msg = f"moved {name} in {source.parent}{s} to {destination.parent}{s}\n"
    return move_msg

def error_message(table_entry, source: Path, short_paths: bool, sep: str, **kwargs):
    """Compose a message describing the movement error
    If short_paths=True, then the source path will be shortened to base_dir
    - table_entry must have the following attributes: name, flag
    - sep is the path delimiter that will be used in the returned message
    - if short_paths is True, the following keyword arguments must be provided:
      - reorgpath: Path
      - shorten_index: int"""
    s = sep

    # Determine the type of issue
    issues = {'d': 'Duplicate', 'm': 'Misplaced', 'u': 'Unclear', 'n': 'Unnecessary'}
    issue_type = issues.get(table_entry.flag, 'Issue') #returns 'Issue' if flag is not 'd' or 'u'
    
    # Add leading and trailing backslashes to directory names
    if source.is_dir():
        name = f"{s}{table_entry.name}{s}"
    else:
        name = source.name

    # If necessary, obtain short path parameters
    if short_paths:
        try:
            comparepath = kwargs['reorgpath']
            shorten_index = kwargs['shorten_index']
        except KeyError:
            print('Warning: parameters \'reorgpath\' and \'shorten_index\' not provided in move_and_log.error_message(). Using full paths...')
            short_paths = False
    
    # Compose error message
    if short_paths:
        try:
            source_parent_for_print = f"{s}{path_from_common_parent(source.parent, comparepath, shorten_index)}{s}"
        except IndexError:
            source_parent_for_print = f"{source.parent}{s}"
        error_msg = f"{issue_type}: {name} in {source_parent_for_print}"
    else:
        error_msg = f"{issue_type}: {name} in {source.parent}{s}"
    return error_msg

def log_message(log_file_path: Path, time, message):
    """Write a timestamped message to a logfile"""
    with log_file_path.open(mode='a') as log_file:
            log_file.write(time + ' --- ' + message)

class MoveError(Exception):
    pass