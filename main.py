# This script reads the contents of a text file and brings up a dialog box
# that displays all of the contents and allows the user to change them
# Ref: https://pythonguides.com/python-tkinter-table-tutorial/
# Ref: https://stackoverflow.com/questions/18562123/how-to-make-ttk-treeviews-rows-editable
# Ref: https://stackoverflow.com/questions/34699583/how-to-get-all-objects-in-a-window-with-their-settings
# Ref: https://stackoverflow.com/questions/60954478/tkinter-treeview-doesnt-resize-with-window

# To Do:
#   modify code to accommodate cat3
#   consider where to put configuration code - before button click or after?
#   have a function quickly check to see if all entries actually exist when button is clicked
#   remove unnecessary imports in main and modules
#   optional: add frame to GUI showing the trello parameters in config
#   optional: add a frame to GUI showing current working directory and base reorg
#   optional: reformat docstrings according to PEP8
#   optional: refactor code so that if users input different column_names the namedtuple referencing does not break

# Note: add , highlightbackground='red', highlightthickness=1 to widget options to see borders

from pathlib import Path
import tkinter as tk
from tkinter import ttk
import trello
import move_and_log
from collections import namedtuple
import time
import ruamel.yaml
import os

def list_names(current_dir: Path):
    '''Returns a list of the absolute paths of the items in current_dir,
    with directories before files'''
    dirs = [p.name for p in current_dir.iterdir() if p.is_dir()]
    files = [p.name for p in current_dir.iterdir() if p.is_file()]
    contents = dirs + files
    return contents

class Table:
    def __init__(self, parent, row_names, column_names, column_widths, heading_names):
        # Initialize Treeview
        self.tree = ttk.Treeview(parent, height=15)
        self.tree.grid(row=0, column=0, columnspan=2, sticky='n')

        # Initialize instance attributes
        self.row_names = row_names
        self.column_names = column_names
        self.column_widths = column_widths
        self.heading_names = heading_names

        # Create columns and headings
        self.tree['columns']= tuple(self.column_names[1:])  #used for indexing, first name omitted because it is always set to #0

        self.tree.column("#0", width=self.column_widths[0], stretch='yes')    #first column and heading must be separately defined
        self.tree.heading("#0", text=self.heading_names[0], anchor='center')   #this column is special because it can be used to display a tree with nested elements

        self.tree.column(self.column_names[1], width=self.column_widths[1], anchor='center', stretch='yes')  #define flag column separately with center anchor
        self.tree.heading(self.column_names[1], text=self.heading_names[1],anchor='center')

        for i in range(2,len(self.column_names)):
            self.tree.column(self.column_names[i], width=self.column_widths[i], anchor='w', stretch='no')
            self.tree.heading(self.column_names[i], text=self.heading_names[i],anchor='center')

        # Add Data
        self.default_values = tuple('' for name in range(1,len(column_names)))
        for name in self.row_names:
            self.tree.insert(parent='',index='end',text=name,values=self.default_values,tags=('clickable'))
                                                                                                        #TODO: add a scrollbar
        # Add event handler to enable cell editing
        self.tree.bind("<Double-1>", self.make_popup)
        self.tree.bind("<Delete>", self.delete_rows)

    def make_popup(self, event):
        ''' Executed, when a row is double-clicked. Opens 
        read-only EntryPopup above the item's column, so it is possible
        to select text '''

        # What row and column was clicked on
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_num = int(col_id[1:])     #remove # and convert to int, to use for indexing 'values' below

        # Get column position info
        x,y,width,height = self.tree.bbox(row_id, col_id)

        # Y-axis offset
        pady = height // 2

        # Get text from current cell
        if col_id =='#0':
            text = self.tree.item(row_id, 'text')
        else:
            text = self.tree.item(row_id, 'values')[col_num-1]
        
        # Create entry popup
        self.entryPopup = EntryPopup(self.tree, row_id, col_num, text, name=('ep_'+row_id+'_'+col_id))

        # Place Entry popup properly
        self.entryPopup.place( x=x, y=y+pady, width=width, height=height, anchor='w') #TODO: use relwidth param to make entrypopup size change dynamically with columns

        # Make text entry for the flag column centered
        if col_id == "#1":
            self.entryPopup['justify'] = 'center'

    def delete_rows(self, event):
        '''deletes the currently selected rows'''
        current_items = self.tree.selection()   #TODO: should I use tree.focus() instead?
        for item in current_items:
            self.tree.delete(item)

class EntryPopup(tk.Entry):
    def __init__(self, parent, row_id, col_num, text, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.parent = parent
        self.row_id = row_id
        self.col_num = col_num

        self.insert(0, text) 
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Escape>", lambda *ignore: self.destroy())       #destroy() accepts no arguments so anonymous function is necessary
        self.bind("<Return>", lambda *ignore: self.insert_text_and_destroy())         #* means this will work for any number of potential arguments
        self.bind("<FocusOut>", lambda *ignore: self.insert_text_and_destroy())
        self.bind("<Control-a>", self.select_all)

    def insert_text_and_destroy(self, *ignore):
        ''' Add the text in EntryPopup to the corresponding cell in parent'''
        if self.col_num == 0:                        #value for col 0 is in 'text'
            self.parent.item(self.row_id, text=self.get())
        else:                                   #Note: there has to be a more elegant way of modifying current row's values than calling item() twice
            current_item = self.parent.item(self.row_id)
            values = current_item['values']
            values[self.col_num-1] = self.get()
            self.parent.item(self.row_id, values=values)
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # Return 'break' to interrupt default key-bindings
        return 'break'

class MainApplication:
    def __init__(self, parent, config_path, column_names, column_widths, heading_names):
        self.parent = parent
        self.config_path = config_path
        
        # Check for input errors
        if not len(column_names) == len(column_widths) == len(heading_names):
            print("Error: column_names, column_widths, and heading_names must be lists of identical length")
            self.exit_app()

        # Import config
        self.config = self.load_config(self.config_path)
        
        # Initialize Data
        self.row_names = list_names(current_dir=Path.cwd())
        self.column_names = column_names
        self.column_widths = column_widths
        self.heading_names = heading_names

        # Create table frame
        self.tableframe = tk.Frame(self.parent)
        self.tableframe.grid(row=0, column=0, columnspan=2, sticky='n')
        
        # Create table (note that packing of table happens inside the class - could be brought outside if Table was a subclass of ttk.Treeview)
        self.table = Table(self.tableframe, self.row_names, self.column_names, self.column_widths, self.heading_names)

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self.tableframe, orient='vertical', command=self.table.tree.yview)
        self.scrollbar.grid(row=0, column=2, sticky='ns')
        self.table.tree.configure(yscrollcommand=self.scrollbar.set)

        # Create info frame
        self.infoframe = tk.Frame(self.parent, width=750, height=100)
        self.infoframe.grid(row=1, column=0, columnspan=3, sticky='ns', pady=5)

        # Create info labels and messages
        self.cwdlabel = tk.Label(self.infoframe, text='Current Directory:\t', font='Calibri 10 bold')
        self.cwdlabel.grid(row=0, column=0, sticky='n')
        self.cwdmessage = tk.Message(self.infoframe, text=str(Path.cwd()), width=750, justify='left')
        self.cwdmessage.grid(row=0, column=1, sticky='w')

        bdtext = 'Base Directory:\t\t' + self.config['BASE_DIRECTORY']
        self.bdlabel = tk.Label(self.infoframe, text='Base Directory:\t', font='Calibri 10 bold')
        self.bdlabel.grid(row=1, column=0, sticky='n')
        self.bdmessage = tk.Message(self.infoframe, text=self.config['BASE_DIRECTORY'], width=750, justify='left')
        self.bdmessage.grid(row=1, column=1, sticky='w')

        self.rdlabel = tk.Label(self.infoframe, text='Reorg Directory:\t', font='Calibri 10 bold')
        self.rdlabel.grid(row=2, column=0, sticky='n')
        self.rdmessage = tk.Message(self.infoframe, text=self.config['REORG_DIRECTORY'], width=750, justify='left')
        self.rdmessage.grid(row=2, column=1, sticky='w')
        
        instructions=('For each item, enter category names to move it to <base>\\<reorg>\\<cat1>\\<cat2>\\<cat3>\n\n' +
                      'Items can be flagged to indicate an issue. A flagged item will not be moved, and a trello card will be created. ' +
                      'Flags can be \'d\' (duplicate), \'u\' (unclear) or any other character (issue)')
        self.messagebox = tk.Message(self.infoframe, text=instructions, width=750, justify='left')
        self.messagebox.grid(row=3, column=0, columnspan=2, sticky='ns')

        # Create button frame
        self.buttonframe = tk.Frame(self.parent)
        self.buttonframe.grid(row=2, column=0, columnspan=2)

        # Create buttons
        self.process_button = tk.Button(self.buttonframe,text="Process",command=self.process_entries)
        self.process_button.grid(row=0, column=0)
        self.exit_button = tk.Button(self.buttonframe, text="Exit", command=self.exit_app)
        self.exit_button.grid(row=0, column=1)

    def exit_app(self):
        '''Close the main window'''
        self.parent.destroy()

    def process_entries(self):
        # Close all EntryPopups that are still open
        popups = [widget for widget in self.table.tree.winfo_children() if widget.winfo_class()=='Entry']
        for p in popups:
            p.insert_text_and_destroy()
        
        # Compose data structure            TODO: make this more elegant
        TableEntry = namedtuple("TableEntry", ' '.join(self.column_names))
        row_ids = self.table.tree.get_children()
        row_ids_for_processing = [
            id 
            for id 
            in row_ids 
            if (self.table.tree.item(id)['values'][0] != '' or    #flag exists
                (self.table.tree.item(id)['values'][1] != '' and  #cat1 and cat2 exist
                self.table.tree.item(id)['values'][2] != ''))
        ]
        table_entries = (
            TableEntry(self.table.tree.item(id)['text'], *self.table.tree.item(id)['values'])
            for id 
            in row_ids_for_processing
        )

        # Move the files and write to log
        for e in table_entries:
            # Current time will be used in log messages  TODO: put this inside the log_message function
            current_time = time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(time.time()))
            
            #paths for movement
            source = Path.cwd() / e.name
            if e.cat3 != '':
                destination = Path(self.config['REORG_DIRECTORY']) / e.cat1 / e.cat2 / e.cat3 / source.name
            else:
                destination = Path(self.config['REORG_DIRECTORY']) / e.cat1 / e.cat2 / source.name

            if e.flag == '':
                # Move and log
                move_and_log.move(source=source,
                                  destination=destination, 
                                  base_dir=Path(self.config['BASE_DIRECTORY']),
                                  sep=os.sep) #TODO: make exception for when cat3 does not exist
                
                msg = move_and_log.move_message(source=source, 
                                                destination=destination, 
                                                base_dir=Path(self.config['BASE_DIRECTORY']),
                                                sep=os.sep)
                
                move_and_log.log_message(log_file_path=Path(self.config['CHANGE_LOG_PATH']), 
                                         time=current_time, 
                                         message=msg)

            else:
                if source.is_dir():
                    print(f"Issue found at {source}{os.sep}")
                else:
                    print(f"Issue found at {source}")
                # Log the error
                msg = move_and_log.error_message(table_entry=e,
                                                 source=source,
                                                 base_dir=Path(self.config['BASE_DIRECTORY']),
                                                 short_paths=False,
                                                 sep=os.sep)
                move_and_log.log_message(log_file_path=Path(self.config['ERROR_LOG_PATH']), 
                                         time=current_time, 
                                         message=msg)

                # Make an issue card
                card_name = move_and_log.error_message(table_entry=e,
                                                 source=source,
                                                 base_dir=Path(self.config['BASE_DIRECTORY']),
                                                 short_paths=True,
                                                 sep=os.sep)
                trello.create_card(list_id=self.config['LIST_ID'], 
                                   card_name=card_name, 
                                   card_description=e.issue_message,
                                   member_ids=self.config['MEMBER_IDS'], 
                                   api_key=self.config['API_KEY'], 
                                   oath_token=self.config['OATH_TOKEN'])

        # Remove the rows that were processed from the table
        for id in row_ids_for_processing:
            self.table.tree.delete(id)
        
        # Exit window if all rows were processed
        # Note: could also use len(row_ids) == len(row_ids_for_processing)
        if self.table.tree.get_children() == ():
            self.exit_app()

    def load_config(self, config_path):
        '''Loads settings from a YAML configuration file, checks to make sure 
        all IDs are present, and then returns the settings as a dictionary'''
        with open(config_path) as config_file:
            yaml = ruamel.yaml.YAML()
            config = yaml.load(config_file)

        # Check that trello credentials are present, and if they aren't throw an error
        if (config['API_KEY'] == None or config['OATH_TOKEN'] == None):
            raise ConfigError(f'trello credential(s) missing in {config_path}')

        # Check that required names are present, and if they aren't throw an error
        if (config['BOARD_NAME'] == None or config['LIST_NAME'] == None):
            raise ConfigError(f'name(s) missing in {config_path}')

        # Check that all paths are present, and if they aren't throw an error
        if (config['ERROR_LOG_PATH'] == None or
            config['CHANGE_LOG_PATH'] == None or
            config['BASE_DIRECTORY'] == None or
            config['REORG_DIRECTORY'] == None):

            raise ConfigError(f'path(s) missing in {config_path}')
            
        # Check that all IDs are present, and if they aren't...
        if (config['BOARD_ID'] == None or
            config['LIST_ID'] == None or
            (config['MEMBER_IDS'] == None and config['MEMBER_NAMES'] != None)):
            
            # Find them...
            print(f'Warning: ID(s) missing in {config_path}. Attempting to find IDs...')
            config['BOARD_ID'] = trello.find_board(config['BOARD_NAME'], config['API_KEY'], config['OATH_TOKEN'])
            config['LIST_ID'] = trello.find_list(config['BOARD_ID'], config['LIST_NAME'], config['API_KEY'], config['OATH_TOKEN'])
            config['MEMBER_IDS'] = trello.find_members(config['MEMBER_NAMES'], config['API_KEY'], config['OATH_TOKEN'])
            
            # Write them to the config file...
            with open(config_path, 'w') as config_file:
                yaml = ruamel.yaml.YAML()
                yaml.dump(config, config_file)

            # And reload the config file
            with open(config_path) as config_file:
                yaml = ruamel.yaml.YAML()
                config = yaml.load(config_file)
        
        return config

class ConfigError(Exception):
    pass

if __name__ == "__main__":
    # Initialize main window
    root=tk.Tk()
    root.title('Reorganize with Trello')
    root.geometry('795x500')

    # Enable resizing of main window contents
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Create GUI
    MainApplication(parent=root, 
                    config_path=Path(__file__).parent / 'testconfig.yml',
                    column_names=['name', 'flag', 'cat1', 'cat2', 'cat3', 'issue_message'],
                    column_widths=[250, 35, 80, 80, 80, 250],
                    heading_names=['name', 'flag', 'cat1', 'cat2', 'cat3 (opt.)', 'issue message'])

    # Run application
    root.mainloop()