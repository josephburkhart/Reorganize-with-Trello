# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 14:47:00 2021

@author: Joseph
Functions for finding boards, lists, users, and for making cards in Trello
"""
from pathlib import Path
import requests

def find_board(board_name, API_KEY, OATH_TOKEN):
    """Returns the ID that corresponds to the given board name"""
    print(f"Searching for board \'{board_name}\'...", end="")
    
    #construct and send the request
    url = "https://api.trello.com/1/members/me/boards/"
    querystring = {"key": API_KEY, "token": OATH_TOKEN}
    response = requests.request("GET", url, params=querystring) #returns a JSON object with info on all the boards for the given Trello account
    
    board_info = next(board for board in response.json() if board["name"] == board_name)   #search the response for the correct board and get its info as a dictionary object
    
    #parse the response to see if the request was successful
    try: 
        board_id = board_info["id"]         #board_id = response.json()[0]["id"] works if there are no other boards
        print("Found\n")
        return board_id
    except:
        print("Error: board not found\n")
        return

def find_list(board_id, list_name, API_KEY, OATH_TOKEN):
    """Returns the ID that corresponds to a given list name and on a board with a given id"""
    print(f"Searching for list \'{list_name}\'...", end="")
    
    #construct and send the request
    url = "https://api.trello.com/1/boards/" + board_id + "/lists"
    querystring = {"key": API_KEY, "token": OATH_TOKEN}
    response = requests.request("GET", url, params=querystring) #returns a JSON object with info on all the lists for the given board

    list_info = next(list_ for list_ in response.json() if list_["name"] == list_name) #trailing underscore to avoid conflict with Python keyword
    
    #parse the response to see if the request was successful
    try:
        list_id = list_info["id"]   #this will return an error if the response contains an error
        print("Found\n")
        return list_id
    except:
        print("Error: list not found \n")
        return
    
def find_members(members: list, API_KEY, OATH_TOKEN):
    """Returns a list of IDs corresponding to a list of usernames"""
    member_ids = []         #list that will hold the member ids
    
    #Find the ID for each member in the list
    for member in members:
        print(f"Searching for member \'{member}\'...", end="")
        
        #construct and send the request
        url = "https://api.trello.com/1/members/" + member
        querystring = {"key": API_KEY, "token": OATH_TOKEN}
        response = requests.request("GET", url, params=querystring) #returns a JSON object with info on all of the members specified
        
        #parse the response to see if the request was successful
        try:
            member_id = response.json()["id"]   #this will return an error if the response contains an error
            member_ids.append(member_id)
            print("Found")
        except:
            print("Error: member not found")
    
    #print confirmation of success or partial success to the console
    if len(member_ids) == len(members):
        print ("All members found \n") 
    else:
        print("Warning: some members not found. Continuing... \n")
    
    return member_ids
  
def create_card(list_id, card_name, card_description, member_ids: list, API_KEY, OATH_TOKEN):
    """Makes a Trello card in the specified list, with a specified name and description"""
    print(f"Creating card \'{card_name}\'...", end="")
    
    #construct and send the request
    url = "https://api.trello.com/1/cards/"
    querystring = {"key": API_KEY, "token": OATH_TOKEN, "name": card_name, "desc": card_description,
                   "pos": "top", "idList": list_id, "idMembers": member_ids}
    response = requests.request("POST", url, params=querystring) #returns a JSON object with info on the newly-created card
    
    #parse the response to see if the request was successful
    try:
        card_id = response.json()["id"]     #this will return KeyError if the response contains an error
        print("Done")
        return card_id
    except:
        print("Error: card not created")
        return
