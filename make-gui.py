# This script reads the contents of a text file and brings up a dialog box
# that displays all of the contents and allows the user to change them
# Ref: https://pythonguides.com/python-tkinter-table-tutorial/
# Ref: https://stackoverflow.com/questions/18562123/how-to-make-ttk-treeviews-rows-editable

from pathlib import Path
import tkinter as tk
from tkinter import ttk
import csv

def parse_text_file(file_path: Path):
    lines = file_path.read_text().splitlines()
    lines = [Path(line[1:-1]) for line in lines] #we want substrings in order to remove quotation marks
    return lines

class Table:
    def __init__(self, parent, row_names, column_names, column_widths):
        #Initialize Treeview
        self.tree = ttk.Treeview(parent)
        self.tree.grid(row=0, column=0, columnspan=2, sticky='n')

        #Initialize instance attributes
        self.column_names = column_names
        self.column_widths = column_widths
        self.row_names = row_names

        # create columns and headings
        self.tree['columns']= tuple(self.column_names[1:])  #used for indexing, first name omitted because it is always set to #0

        self.tree.column("#0", width=self.column_widths[0], stretch=tk.YES)    # first column and heading must be separately defined
        self.tree.heading("#0", text=self.column_names[0], anchor=tk.CENTER)   # this column is special because it can be used to display a tree with nested elements

        self.tree.column(self.column_names[1], width=self.column_widths[1], anchor=tk.CENTER, stretch=tk.YES)  # define flag column separately with center anchor
        self.tree.heading(self.column_names[1],text=self.column_names[1],anchor=tk.CENTER)

        for i in range(2,len(self.column_names)):
            self.tree.column(self.column_names[i], width=self.column_widths[i], anchor=tk.W, stretch=tk.NO)
            self.tree.heading(self.column_names[i],text=self.column_names[i],anchor=tk.CENTER)

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

        # what row and column was clicked on    TODO: make this part not allow editing of paths in column 1
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_num = int(col_id[1:]) #remove # and convert to int, to use for indexing 'values' below

        # get column position info
        x,y,width,height = self.tree.bbox(row_id, col_id)

        # y-axis offset
        pady = height // 2

        # get text from current cell
        if col_id =='#0':
            text = self.tree.item(row_id, 'text')
        else:
            text = self.tree.item(row_id, 'values')[col_num-1]
        
        # create entry popup
        self.entryPopup = EntryPopup(self.tree, row_id, col_num, text)

        # place Entry popup properly
        self.entryPopup.place( x=x, y=y+pady, width=width, height=height, anchor=tk.W) #TODO: use relwidth param to make entrypopup size change dynamically with columns

        # make text entry for the flag column centered
        if col_id == "#1":
            self.entryPopup['justify'] = 'center'

    def delete_rows(self, event):
        '''deletes the currently selected rows'''
        current_items = self.tree.selection()   #TODO: should I use tree.focus() instead?
        for item in current_items:
            self.tree.delete(item)

    def select_item(self, event):
        '''gets information about the currently selected cell in treeview
        Ref: https://stackoverflow.com/questions/48268506/select-a-cell-in-tkinter-treeview-and-get-the-cell-data'''
        curItem = self.tree.item(self.tree.focus()) #this returns a dict, such as {'text': '', 'image': '', 'values': ['C:\\Users\\Joseph\\computer\\pythonsandbox\\ReorgKADTest\\make_key_selectfilestest.py', '', ''], 'open': 0, 'tags': ['clickable']}
        col = self.tree.identify_column(event.x)
        col_num = int(col[1:]) #remove the # symbol
        print ('curItem = ', curItem)
        print ('col_num = ', col_num)

        cell_value = curItem['values'][col_num-1]
        print('current value = ', cell_value)

class EntryPopup(tk.Entry):

    def __init__(self, parent, iid, col_num, text, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.parent = parent
        self.iid = iid          #this is just row_id
        self.col_num = col_num

        self.insert(0, text) 
        self['exportselection'] = False #TODO: remove??

        self.focus_force()
        self.bind("<Escape>", lambda *ignore: self.destroy())       #destroy() accepts no arguments so anonymous function is necessary
        self.bind("<Return>", self.insert_text_and_destroy)         #* means this will work for any number of potential arguments
        self.bind("<FocusOut>", self.insert_text_and_destroy)
        self.bind("<Control-a>", self.select_all)

    def insert_text_and_destroy(self, event):
        ''' Add the text in EntryPopup to the corresponding cell in parent'''
        if self.col_num == 0:                        #value for col 0 is in 'text'
            self.parent.item(self.iid, text=self.get())
        else:                                   #Note: there has to be a more elegant way of modifying current row's values than calling item() twice
            current_item = self.parent.item(self.iid)
            values = current_item['values']
            values[self.col_num-1] = self.get()
            self.parent.item(self.iid, values=values)
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'

class MainApplication:
    def __init__(self, parent):
        self.parent = parent
        
        # Initialize Data
        self.row_names = [
            "C:\\testdir\\testfile1.txt",
            "C:\\testdir\\testfile2.tex",
            "C:\\testdir\\testfile3.py"
        ]
        self.column_names = ['filename', 'flag', 'cat1']
        self.column_widths = [250, 70, 80]

        # Create table (note that packing of table happens inside the class - could be brought outside if Table was subclass of Treeview)
        self.tableframe = tk.Frame(self.parent)
        self.tableframe.grid(row=0, column=0, columnspan=2, sticky='n')
        
        self.table = Table(self.tableframe, self.row_names, self.column_names, self.column_widths)

        # Create frame
        self.bottomframe = tk.Frame(self.parent)
        self.bottomframe.grid(row=1, column=0, columnspan=2)

        # Create buttons
        self.save_button = tk.Button(self.bottomframe,text="Save",command=self.save_entries)
        self.save_button.grid(row=1, column=0)
        self.exit_button = tk.Button(self.bottomframe, text="Exit", command=self.exit_app)
        self.exit_button.grid(row=1, column=1)

    def save_entries(self):
        '''Export each entry in the table to a csv file 
        (will be changed later to just return entries as a list of lists)'''
        #data = []   #TODO: better to make a class with the different attribute names
        with open('data.csv', 'w', newline='') as myfile:
            csvwriter = csv.writer(myfile, delimiter=',')
        
            for row_id in self.table.tree.get_children():
                row = [self.table.tree.item(row_id)['text']]        #first column
                row.extend(self.table.tree.item(row_id)['values'])  #remaining columns
                print('save row: ', row)
                csvwriter.writerow(row)

    def exit_app(self):
        '''Close the main window'''
        self.parent.destroy()

if __name__ == "__main__":
    # Initialize main window
    root=tk.Tk()
    root.title('Reorganize with Trello')
    root.geometry('500x500')

    # Create GUI
    MainApplication(root)

    # Run application
    root.mainloop()