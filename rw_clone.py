#!/usr/bin/python3
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

textview = Gtk.TextView()

# create main window
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
        self.pci_liststore = Gtk.ListStore(str, str, str, str)
        for pci_ref in pci_list:
            self.pci_liststore.append(list(pci_ref))

        #creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView(self.pci_liststore)
        for i, column_title in enumerate(["BDF", "Desc","VID", "DID"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        # set up listener for click
        self.treeview.connect("row-activated", self.on_device_selected)
        # self.treeview.connect("cursor-changed", self.on_device_changed)

        #setting up the layout, putting the treeview in a scrollwindow
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 8, 10)
        self.scrollable_treelist.add(self.treeview)

        # add text view for lspci output
        # textview = Gtk.TextView()
        textview.get_buffer().insert_at_cursor('No device selected')
        self.grid.attach(textview,0,5,8,5)
        self.show_all()

    # def on_device_changed(path, user_data):
        # print()
        # print(path)
        # print(user_data)
        # selection = user_data.get_selection()
        # print(selection)
        # row = selection.get_selected_rows()[0]
        # print(row)
        # iter1 = row.get_iter(path)
        # print(iter1)
        # pci_bdf = row.get_value(iter1,0)
        # print(pci_bdf)

    # when a row is selected, pop up a new window with config space in it
    def on_device_selected(treeview, iter, path, user_data):
        model = iter.get_selection().get_selected_rows()[0]
        iter1 = model.get_iter(path)
        pci_bdf = model.get_value(iter1,0)
        bus = pci_bdf.split(':')[0]
        dev = pci_bdf.split('.')[0].split(':')[1]
        fun = pci_bdf.split('.')[1]
        # print('bus: %s dev: %s fun: %s' % (bus,dev,fun))
        # print(pci_bdf)
        # print(path)

        textview.get_buffer().set_text('')
        cmd = subprocess.Popen('lspci -vvv -s %s:%s.%s' % (bus,dev,fun), shell=True, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            textview.get_buffer().insert_at_cursor(line.decode('ascii'))

        configEditor = configSpaceEditWindow(bus, dev, fun)

class configSpaceEditWindow(Gtk.Window):

    def __init__(self, bus, dev, fun):
        Gtk.Window.__init__(self, title="Edit PCI config space - Device %s:%s.%s" % (bus,dev,fun))
        self.set_border_width(10)
        self.resize(1200,400)

        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        #Creating the ListStore model
        self.int_liststore = Gtk.ListStore(str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str)

        # populate with data
        self.populate(bus,dev,fun)

        #creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView(self.int_liststore)
        for i, column_title in enumerate(["offset","0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)

            # if not offset column, make cell editable
            if i!=0:
                renderer.connect('edited', self.cell_edited_callback, i, bus, dev, fun)
                renderer.set_property('editable', True)

            self.treeview.append_column(column)

        #setting up the layout, putting the treeview in a scrollwindow
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 8, 10)
        self.scrollable_treelist.add(self.treeview)

        # set up listener for click
        self.treeview.connect("row-activated", self.on_device_selected)

        self.show_all()

    def populate(self,bus,dev,fun):
        self.int_liststore.clear()
        for item in self.getConfigSpace(bus,dev,fun):
            self.int_liststore.append(item)

    def cell_edited_callback(configSpaceEditWindow, CellRendererText, row, new_text, col, bus, dev, fun):
        orig_text = CellRendererText.get_property('text')
        # print(configSpaceEditWindow)
        # print(CellRendererText)
        if orig_text != new_text :
            offset = (int(row)*16) + (col-1)
            print('write to BDF %s:%s.%s, offset 0x%02X from %s to %s' % (bus,dev,fun,offset,orig_text,new_text))
            cmd = subprocess.Popen('xxd /sys/devices/pci0000:%s/0000:%s:%s.%s/config' % (bus,bus,dev,fun), shell=True, stdout=subprocess.PIPE)
            for line in cmd.stdout:
                print(line.decode('ascii'))


    def getConfigSpace( self, bus, dev, fun):
        cmd = subprocess.Popen('lspci -xxxx -s %s:%s.%s' % (bus,dev,fun), shell=True, stdout=subprocess.PIPE)
        # list to store pci devices
        int_list = []

        # iterate over lspci command output and build tuples
        for line in cmd.stdout:
            tup = []
            for field in shlex.split(line.decode('ascii')):
                tup.append(field)
            int_list.append(tuple(tup))

        # throw away first row
        return int_list[1:]

    def on_device_selected(treeview, iter, path, user_data):
        model = iter.get_selection().get_selected_rows()[0]
        iter1 = model.get_iter(path)
        pci_bdf = model.get_value(iter1,0)
        bus = pci_bdf.split(':')[0]
        dev = pci_bdf.split('.')[0].split(':')[1]
        fun = pci_bdf.split('.')[1]
        # print('bus: %s dev: %s fun: %s' % (bus,dev,fun))




# instantiate GUI
win = TreeViewFilterWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
