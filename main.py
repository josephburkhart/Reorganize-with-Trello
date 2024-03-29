# This script generates a list of all the items in the current directory,
# creates a UI in which the user can flag items or sort them into categories,
# and then processes the items according to the user's input
# Ref: https://pythonguides.com/python-tkinter-table-tutorial/
# Ref: https://stackoverflow.com/questions/18562123/how-to-make-ttk-treeviews-rows-editable
# Ref: https://stackoverflow.com/questions/34699583/how-to-get-all-objects-in-a-window-with-their-settings
# Ref: https://stackoverflow.com/questions/60954478/tkinter-treeview-doesnt-resize-with-window
# Note: add , highlightbackground='red', highlightthickness=1 to widget options to see borders

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import trello
import move_and_log
from collections import namedtuple
import time
import configparser
import os

def list_names(current_dir: Path):
    """Returns a list of the absolute paths of the items in current_dir,
    with directories before files"""
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
        self.column_ids = ['#'+str(i) for i in range(len(column_names))]
        self.column_widths = column_widths
        self.heading_names = heading_names

        # Create columns and headings
        self.tree['columns']= tuple(self.column_names[1:])  #used for indexing, first name omitted because it is always set to #0

        for i in range(len(self.column_names)):
            self.tree.column(self.column_names[i], width=self.column_widths[i], anchor='w', stretch='no')
            self.tree.heading(self.column_names[i], text=self.heading_names[i],anchor='center')

        self.tree.column(self.column_names[1], anchor='center') #center the text in the flag column

        # Add Data
        self.default_values = tuple('' for name in range(1,len(column_names)))
        for name in self.row_names:
            self.tree.insert(parent='',index='end',text=name,values=self.default_values,tags=('clickable'))

        # Add event handler to enable cell editing
        self.tree.bind("<Double-1>", self.make_popup)
        self.tree.bind("<Delete>", self.delete_rows)

    def make_popup(self, event):
        """ Executed, when a row is double-clicked. Opens 
        read-only EntryPopup above the item's column, so it is possible
        to select text """

        # What row and column was clicked on
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_index = int(col_id[1:])     #remove # and convert to int, to use for indexing 'values' below
        # print(col_id)
        # print(self.tree.column('flag'))
        
        # Get column position info
        x,y,width,height = self.tree.bbox(row_id, col_id)

        # Y-axis offset
        pady = height // 2

        # Get text from current cell
        if col_index == 0:
            text = self.tree.item(row_id, 'text')
        else:
            text = self.tree.item(row_id, 'values')[col_index-1]
        
        # Create entry popup
        self.entryPopup = EntryPopup(self.tree, self, row_id, col_index, text, name=('ep_'+row_id+'_'+col_id))

        # Place Entry popup properly
        self.entryPopup.place( x=x, y=y+pady, width=width, height=height, anchor='w') #TODO: use relwidth param to make entrypopup size change dynamically with columns

        # Make text entry for the flag column centered
        if col_id == "#1":
            self.entryPopup['justify'] = 'center'

    def delete_rows(self, event):
        """deletes the currently selected rows"""
        current_items = self.tree.selection()   #TODO: should I use tree.focus() instead?
        for item in current_items:
            self.tree.delete(item)

class EntryPopup(tk.Entry):
    def __init__(self, parent, grandparent, row_id, col_index, text, **kw):
        """ If relwidth is set, then width is ignored """
        # Initialize instance attributes
        super().__init__(parent, **kw)
        self.parent = parent
        self.grandparent = grandparent
        self.row_id = row_id
        self.col_index = col_index

        # Add text from parent
        self.insert(0, text)

        # Adjust final settings
        self['exportselection'] = False
        self.focus_force()

        # Event Handlers
        self.bind("<Escape>", lambda *ignore: self.destroy())       #destroy() accepts no arguments so anonymous function is necessary
        self.bind("<Return>", lambda *ignore: self.insert_text_and_destroy())         #* means this will work for any number of potential arguments
        self.bind("<FocusOut>", lambda *ignore: self.insert_text_and_destroy())
        self.bind("<Control-a>", self.select_all)
        self.bind("<Tab>", lambda event, inc=1: self.next_entry(event, inc))
        self.bind("<Shift-Tab>", lambda event, inc=-1: self.next_entry(event, inc))

    def insert_text_and_destroy(self, *ignore):
        """ Add the text in EntryPopup to the corresponding cell in parent"""
        if self.col_index == 0:                        #value for col 0 is in 'text'
            self.parent.item(self.row_id, text=self.get())
        else:                                   #Note: there has to be a more elegant way of modifying current row's values than calling item() twice
            current_item = self.parent.item(self.row_id)
            values = current_item['values']
            values[self.col_index-1] = self.get()
            self.parent.item(self.row_id, values=values)
        self.destroy()

    def select_all(self, *ignore):
        """ Set selection on the whole text """
        self.selection_range(0, 'end')

        # Return 'break' to interrupt default key-bindings
        return 'break'
    
    def next_entry(self, event, inc: int):
        """ Allow the user to move from one EntryPopup to the next across rows and columns.
        `inc` is the increment (+/- int) by which the column and row position is changed."""
        # Calculate IDs
        row_ids = self.parent.get_children()
        row_index = row_ids.index(self.row_id)
        col_ids = self.grandparent.column_ids
        col_index = self.col_index

        if ((col_index+inc) > len(col_ids)-1) or ((col_index+inc) < 0):
            col_index = (col_index+inc) % len(col_ids)
            if ((row_index+inc) > len(row_ids)-1) or ((row_index+inc) < 0):
                row_index = (row_index+inc) % len(row_ids)
            else:
                row_index += inc
        else:
            col_index += inc

        row_id = row_ids[row_index]
        col_id = col_ids[col_index]

        # Get column position info
        x,y,width,height = self.parent.bbox(row_id, col_id)

        # Y-axis offset
        pady = height // 2

        # Get text from current cell
        if col_id =='#0':
            text = self.parent.item(row_id, 'text')
        else:
            text = self.parent.item(row_id, 'values')[col_index-1]
        
        # Create new entry popup
        newpopup = EntryPopup(self.parent, self.grandparent, row_id, col_index, text, name=('ep_'+row_id+'_'+col_id))

        # Place new popup properly
        newpopup.place( x=x, y=y+pady, width=width, height=height, anchor='w') #TODO: use relwidth param to make entrypopup size change dynamically with columns

        # Switch focus to new popup (should cause the old one to be immediately destroyed)
        newpopup.focus()

        return 'break'


class MainApplication:
    def __init__(self, parent, config_file_path, error_log_path, change_log_path, column_names, column_widths, heading_names):
        print('Initializing main application...')
        
        # Initialize key attributes
        self.parent = parent
        self.config_file_path = config_file_path
        self.error_log_path = error_log_path
        self.change_log_path = change_log_path

        # Check for input errors
        if not len(column_names) == len(column_widths) == len(heading_names):
            print("Error: column_names, column_widths, and heading_names must be lists of identical length")
            self.exit_app()
        
        # Initialize Column Data
        self.column_names = column_names
        self.column_widths = column_widths
        self.heading_names = heading_names

        # Import configuration settings and flags
        self.settings = self.load_settings(self.config_file_path)
        self.flags = self.load_flags(self.config_file_path)

        # Create GUI
        self.create_gui()
        print('Initialization complete\n')


    def create_gui(self):
        """Create the user interface based on key parameters and data"""
        # Set current working directory
        self.cwd = Path.cwd()
        print(f'Current directory: {self.cwd}{os.sep}') #TODO: make the cnsole output look better

        # Determine row names from current directory
        self.row_names = list_names(current_dir=self.cwd)

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
        self.cwdmessage = tk.Message(self.infoframe, text=str(self.cwd), width=750, justify='left')
        self.cwdmessage.grid(row=0, column=1, sticky='w')

        self.rdlabel = tk.Label(self.infoframe, text='Reorg Directory:\t', font='Calibri 10 bold')
        self.rdlabel.grid(row=2, column=0, sticky='n')
        self.rdmessage = tk.Message(self.infoframe, text=self.settings['REORG_DIRECTORY'], width=750, justify='left')
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
        self.reload_button = tk.Button(self.buttonframe,text="Reload",command=self.reload_with_new_cwd)
        self.reload_button.grid(row=0, column=1)
        self.exit_button = tk.Button(self.buttonframe, text="Exit", command=self.exit_app)
        self.exit_button.grid(row=0, column=2)

    def exit_app(self):
        """Close the main window"""
        print('Shutting down')
        self.parent.destroy()

    def reload_with_new_cwd(self):
        """Prompt user to choose a new working directory, move to it,
        and re-initialize MainApplication"""
        print("Reloading with new working directory: ", end="")
        
        new_cwd = Path(filedialog.askdirectory())
        
        if str(new_cwd) == '.':
            print('no directory chosen')
        else:
            os.chdir(str(new_cwd))
            self.create_gui()

    def process_entries(self):
        print("Processing table entries...\n")

        # Close all EntryPopups that are still open
        popups = [widget for widget in self.table.tree.winfo_children() if widget.winfo_class()=='Entry']
        for p in popups:
            p.insert_text_and_destroy()
        
        # Compose data structure            TODO: make this more elegant
        data_field_names = self.heading_names[:1] + self.column_names[1:]
        TableEntry = namedtuple("TableEntry", ' '.join(data_field_names))
        row_ids = self.table.tree.get_children()
        row_ids_for_processing = [
            id 
            for id 
            in row_ids 
            if (self.table.tree.item(id)['values'][0] != '' or      #flag exists
                self.table.tree.item(id)['values'][1] != '')        #cat1 exists
        ]
        table_entries = []
        for id in row_ids_for_processing:
            table_entries.append(
                TableEntry(self.table.tree.item(id)['text'], *self.table.tree.item(id)['values'])
            )

        # Move the files and write to log
        for i in range(len(table_entries)):
            e = table_entries[i]
            
            # Current time will be used in log messages  TODO: put this inside the log_message function
            current_time = time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(time.time()))
            
            #paths for movement
            source = self.cwd / e.name
            if e.cat3 != '':
                destination = Path(self.settings['REORG_DIRECTORY']) / e.cat1 / e.cat2 / e.cat3 / source.name
            elif e.cat2 !='':
                destination = Path(self.settings['REORG_DIRECTORY']) / e.cat1 / e.cat2 / source.name
            else:
                destination = Path(self.settings['REORG_DIRECTORY']) / e.cat1 / source.name

            # Print status to console
            print(f"Attempting to move {source.name}...")

            # If there is no  flag, attempt the move and skip it if there's a MoveError
            if e.flag == '':
                try:
                    move_and_log.move(source=source,
                                    destination=destination, 
                                    shorten_index=-1,
                                    sep=os.sep)
                except move_and_log.MoveError:
                    row_ids_for_processing.remove(row_ids_for_processing[i])
                    print('Move has been skipped. Continuing...\n')
                    continue
                
                else:                
                    msg = move_and_log.move_message(source=source, 
                                                    destination=destination, 
                                                    sep=os.sep)
                    move_and_log.log_message(log_file_path=self.change_log_path, 
                                            time=current_time, 
                                            message=msg)
            
            # Flag error and log
            else:
                if source.is_dir():
                    print(f"Issue found at {source}{os.sep}")
                else:
                    print(f"Issue found at {source}")

                msg = move_and_log.error_message(table_entry=e,
                                                 issues=self.flags,
                                                 source=source,
                                                 short_paths=False,
                                                 sep=os.sep)
                move_and_log.log_message(log_file_path=self.error_log_path, 
                                         time=current_time, 
                                         message=msg+'\n')

                # Make an issue card
                card_name = move_and_log.error_message(table_entry=e,
                                                       issues=self.flags,
                                                       source=source,
                                                       short_paths=False,
                                                       sep=os.sep,
                                                       reorgpath=Path(self.settings['REORG_DIRECTORY']),
                                                       shorten_index=-1)
                trello.create_card(list_id=self.settings['LIST_ID'], 
                                   card_name=card_name, 
                                   card_description=e.issue_message,
                                   member_ids=self.settings['MEMBER_IDS'], 
                                   api_key=self.settings['API_KEY'], 
                                   oath_token=self.settings['OATH_TOKEN'])

        # Remove the rows that were processed from the table
        for id in row_ids_for_processing:
            self.table.tree.delete(id)
        
        # Exit window if all rows were processed
        # Note: could also use len(row_ids) == len(row_ids_for_processing)
        if self.table.tree.get_children() == ():
            print('All entries have been processed')
            self.reload_with_new_cwd()

    def load_settings(self, config_file_path):
        """Loads keys and options from an INI configuration file, checks to make
        sure all IDs are present, and then returns the settings section of the 
        file as a dictionary"""
        print(f"Loading settings from {config_file_path}")
        config = configparser.ConfigParser(comment_prefixes='/', 
                                   allow_no_value=True,
                                   delimiters='=')
        config.optionxform = lambda option: option
        config.read(config_file_path)

        # Shorthand for the 'Settings' section
        settings = config['Settings']

        # Check that trello credentials are present, and if they aren't throw an error
        if (settings['API_KEY'] == '' or settings['OATH_TOKEN'] == ''):
            raise ConfigError(f'trello credential(s) missing in {config_file_path}')

        # Check that required names are present, and if they aren't throw an error
        if (settings['BOARD_NAME'] == '' or settings['LIST_NAME'] == ''):
            raise ConfigError(f'name(s) missing in {config_file_path}')

        # Check that all paths are present, and if they aren't throw an error
        if settings['REORG_DIRECTORY'] == '':
            raise ConfigError(f'path(s) missing in {config_file_path}')
            
        # Check that all IDs are present, and if they aren't...
        if (settings['BOARD_ID'] == '' or
            settings['LIST_ID'] == '' or
            (settings['MEMBER_IDS'] == '' and settings['MEMBER_NAMES'] != '')):
            
            # Find the BOARD_ID...
            print(f'Warning: ID(s) missing in {config_file_path}. Attempting to find IDs...\n')
            try:
                settings['BOARD_ID'] = trello.find_board(settings['BOARD_NAME'], settings['API_KEY'], settings['OATH_TOKEN'])
            except trello.TrelloError:
                print(f"Error! Board not found: {settings['BOARD_NAME']}. Exiting app...")
                raise SystemExit
            
            # Find the LIST_ID
            try:
                settings['LIST_ID'] = trello.find_list(settings['BOARD_ID'], settings['LIST_NAME'], settings['API_KEY'], settings['OATH_TOKEN'])
            except trello.TrelloError:
                print(f"Error! List not found: {settings['LIST_NAME']}. Exiting app...")
                raise SystemExit
            
            # Find the MEMBER_IDS
            member_names = settings['MEMBER_NAMES'].split(', ')
            member_ids = trello.find_members(member_names, settings['API_KEY'], settings['OATH_TOKEN'])
            settings['MEMBER_IDS'] = ', '.join(member_ids)
            if len(member_ids) == len(member_names):
                print ("All members found\n") 
            else:
                print("Warning! some members not found. Continuing...\n")

            # Write them to the config file
            with open(config_file_path, 'w') as config_file:
                config.write(config_file)

        print('Settings loaded successfully!')
        print(f"Reorganization directory: {settings['REORG_DIRECTORY']}{os.sep}")
        return dict(settings)

    def load_flags(self, config_file_path):
        """Loads keys and options from an INI configuration file, and then 
        returns the flags section of the file as a dictionary"""
        print(f"Loading flags from {config_file_path}")
        config = configparser.ConfigParser(comment_prefixes='/', 
                                   allow_no_value=True,
                                   delimiters='=')
        config.optionxform = lambda option: option
        config.read(config_file_path)
        
        return dict(config['Flags'])

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
                    config_file_path=Path(__file__).parent / 'testconfig.ini',
                    error_log_path=Path(__file__).parent / 'error.log',
                    change_log_path=Path(__file__).parent / 'change.log',
                    column_names=['#0', 'flag', 'cat1', 'cat2', 'cat3', 'issue_message'],
                    column_widths=[250, 35, 80, 80, 80, 250],
                    heading_names=['name', 'flag', 'cat1', 'cat2 (opt.)', 'cat3 (opt.)', 'issue message (opt.)'])

    # Run application
    root.mainloop()