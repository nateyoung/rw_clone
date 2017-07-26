#!/usr/bin/env python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import subprocess
import shlex

cmd = subprocess.Popen('lspci -mmnn', shell=True, stdout=subprocess.PIPE)

# list to store pci devices
pci_list = []

# iterate over lspci command output and build tuples
for line in cmd.stdout:
    tup = []
    for field in shlex.split(line.decode('ascii')):
        tup.append(field)
    pci_list.append(tuple(tup[0:4]))


# create Gtk GUI
class TreeViewFilterWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="PCI Editor")
        self.set_border_width(10)
        self.resize(1200,400)

        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        #Creating the ListStore model
        self.software_liststore = Gtk.ListStore(str, str, str, str)
        for pci_ref in pci_list:
            self.software_liststore.append(list(pci_ref))

        #creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView(self.software_liststore)
        for i, column_title in enumerate(["BDF", "Desc","VID", "DID"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        # set up listener for click
        self.treeview.connect("row-activated", self.on_device_selected)

        #setting up the layout, putting the treeview in a scrollwindow
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 8, 10)
        self.scrollable_treelist.add(self.treeview)

        self.show_all()

    # when a row is selected, pop up a new window with config space in it
    def on_device_selected(treeview, iter, path, user_data):
        model = iter.get_selection().get_selected_rows()[0]
        iter1 = model.get_iter(path)
        print(model.get_value(iter1,0))


# instantiate GUI
win = TreeViewFilterWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
