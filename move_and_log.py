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

def move(source: Path, destination: Path, base_dir: Path):
    '''Moves specified item at source path to destination path,
    printing messages to the console as needed'''
    # Check if the named file/directory exists
    if not source.exists():
        if source.is_dir():
            print(f"Warning: {os.sep}{source.name}{os.sep} does not exist in {source.parent}{os.sep}\nMove has been skipped. Continuing...")
        else:
            print(f"Warning: {source.name} does not exist in {source.parent}{os.sep}\nMove has been skipped. Continuing...")
        return
    
    # Check if there is a duplicate file/directory at the destination
    if destination.exists():
        if source.is_dir():
            print(f"Warning: {os.sep}{source.name}{os.sep} already exists in {destination.parent}{os.sep}\nMove has been skipped. Continuing...")
        else:
            print(f"Warning: {source.name} already exists in {destination.parent}{os.sep}\nMove has been skipped. Continuing...")
        return
    
    # Create destination folder if necessary    TODO: modify print statement to include base reorg directory
    if not destination.parent.exists():
        print(f"Destination does not exist: .{os.sep}{destination.parent.parent.name}{os.sep}{destination.parent.name}{os.sep} \nCreating destination...", end="")
        destination.parent.mkdir(parents=True, exist_ok=False) #all intermediate folders are also created
        print("Done\n")
    
    # If name is a directory, move it with copy_tree 
    if source.is_dir():
        #destination.mkdir(parents=False, exist_ok=False)    
        copy_tree(str(source), str(destination), preserve_times=True)
        shutil.rmtree(source)
        print(f"{os.sep}{source.name}{os.sep} has been moved to .{os.sep}{shorten_path(destination.parent, base_dir)}{os.sep}")
    
    # If name is a file, move it with shutil.move
    else:
        shutil.move(source, destination)
        print(f"{source.name} has been moved to .{os.sep}{shorten_path(destination.parent, base_dir)}{os.sep}")
    return 0

def move_message(source: Path, destination: Path, base_dir: Path):
    '''Compose a message describing the movement
    Note that table_entry must have the following attributes: name'''
    short_source = shorten_path(source, base_dir)
    short_dest = shorten_path(destination, base_dir)
    if source.is_dir():
        move_msg = f"moved {os.sep}{source.name}{os.sep} in {short_source.parent}{os.sep} to {short_dest.parent}{os.sep}\n"
    else:
        move_msg = f"moved {source.name} in {short_source.parent}{os.sep} to {short_dest.parent}{os.sep}\n"
    return move_msg

def error_message(table_entry, current_dir: Path, base_dir: Path):
    '''Compose a message describing the movement error
    Note that table_entry must have the following attributes: name, flag'''
    source = current_dir / table_entry.name
    if source.is_dir():
        print(f"Issue found at {current_dir / table_entry.name}{os.sep}")
    else:
        print(f"Issue found at {current_dir / table_entry.name}")
    
    # Determine the type of issue
    issues = {'d': 'Duplicate', 'u': 'Unclear'}
    issue_type = issues.get(table_entry.flag, 'Issue') #returns 'Issue' if flag is not 'd' or 'u'
    
    # Compose error message
    short_source_parent = shorten_path(source.parent, base_dir)
    if source.is_dir():
        error_msg = f"{issue_type}: {os.sep}{table_entry.name}{os.sep} in .{os.sep}{short_source_parent}{os.sep}"
    else:
        error_msg = f"{issue_type}: {table_entry.name} in .{os.sep}{short_source_parent}{os.sep}"
    return error_msg

def log_message(log_file_path: Path, time, message):
    '''Write a timestamped message to a logfile'''
    with log_file_path.open(mode='a') as log_file:
            log_file.write(time + ' --- ' + message)