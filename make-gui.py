# This script reads the contents of a text file and brings up a dialog box
# that displays all of the contents and allows the user to change them
# Ref: https://pythonguides.com/python-tkinter-table-tutorial/
# Ref: https://stackoverflow.com/questions/18562123/how-to-make-ttk-treeviews-rows-editable

from pathlib import Path
from tkinter import *
from tkinter import ttk
import numpy as np

def parse_text_file(file_path: Path):
    lines = file_path.read_text().splitlines()
    lines = [Path(line[1:-1]) for line in lines] #we want substrings in order to remove quotation marks
    return lines

class Table:
    def __init__(self, parent, row_names, column_names, column_widths):
        #Initialize Treeview
        self.tree = ttk.Treeview(parent)
        self.tree.pack(fill='x')

        #Initialize instance attributes
        self.column_names = column_names
        self.column_widths = column_widths
        self.row_names = row_names

        self.tree['columns']= tuple(self.column_names)
        
        # first column is hidden so all cell contents can be referenced using the values attribute
        self.tree.column("#0", width=0,  stretch=NO)
        self.tree.heading("#0",text="",anchor=CENTER)

        # remaining columns
        for i in range(len(self.column_names)):
            print(self.column_names[i])
            self.tree.column(self.column_names[i], width=self.column_widths[i], anchor=W, stretch=NO)
            self.tree.heading(self.column_names[i],text=self.column_names[i],anchor=CENTER)

        # Add Data
        for name in self.row_names:
            self.tree.insert(parent='',index='end',text='name',values=(name,'',''),tags=('clickable'))   #TODO: make values dependent on number of columns
                                                                                                        #TODO: add a scrollbar
        # Add event handler to enable cell editing
        self.tree.bind("<Double-1>", self.onDoubleClick)

    def onDoubleClick(self, event):
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
        text = self.tree.item(row_id, 'values')[col_num-1]
        self.entryPopup = EntryPopup(self.tree, row_id, text)

        # place Entry popup properly
        self.entryPopup.place( x=x, y=y+pady, width=width, height=height, anchor=W) #TODO: use relwidth param to make entrypopup size change dynamically with columns


    def selectItem(self, event):
        '''gets information about the currently selected cell in treeview
        Ref: https://stackoverflow.com/questions/48268506/select-a-cell-in-tkinter-treeview-and-get-the-cell-data'''
        curItem = self.tree.item(self.tree.focus()) #this returns a dict, such as {'text': '', 'image': '', 'values': ['C:\\Users\\Joseph\\computer\\pythonsandbox\\ReorgKADTest\\make_key_selectfilestest.py', '', ''], 'open': 0, 'tags': ['clickable']}
        col = self.tree.identify_column(event.x)
        col_num = int(col[1:]) #remove the # symbol
        print ('curItem = ', curItem)
        print ('col_num = ', col_num)

        cell_value = curItem['values'][col_num-1]
        print('current value = ', cell_value)

class EntryPopup(Entry):

    def __init__(self, parent, iid, text, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.iid = iid

        self.insert(0, text) 
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):
        self.tv.item(self.iid, text=self.get())
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'

# Initialize Data
row_names = [
    "C:\\testdir\\testfile1.txt",
    "C:\\testdir\\testfile2.tex",
    "C:\\testdir\\testfile3.py"
]
column_names = ['filename', 'flag', 'cat1']
column_widths = [250, 70, 80]

# Create GUI
ROOT=Tk()

ROOT.title('Reorganize with Trello')
ROOT.geometry('500x500')

mytree = Table(ROOT, row_names, column_names, column_widths)

ROOT.mainloop()