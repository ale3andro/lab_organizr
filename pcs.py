#!/usr/bin/python
# -*- coding: utf-8 -*-
from gi.repository import Gtk

def show_warning_window(parent, message):
    dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
    if (dialog.run()==Gtk.ResponseType.OK):
            dialog.destroy()
    return

def show_directory_chooser(parent, message):
    dialog = Gtk.FileChooserDialog(message, parent, Gtk.FileChooserAction.SELECT_FOLDER,
                                   ("Άκυρο", Gtk.ResponseType.CANCEL, "Επιλογή", Gtk.ResponseType.OK))
    response = dialog.run()
    dirname = "-1"
    if response == Gtk.ResponseType.OK:
        dirname = dialog.get_filename()

    dialog.destroy()
    return dirname
    #elif response == Gtk.ResponseType.CANCEL:
    #    return -1


def show_file_chooser(parent, message):
    dialog = Gtk.FileChooserDialog(message, parent, Gtk.FileChooserAction.OPEN,
                                   ("Άκυρο", Gtk.ResponseType.CANCEL, "Επιλογή", Gtk.ResponseType.OK))
    response = dialog.run()
    filename = "-1"
    if response == Gtk.ResponseType.OK:
        filename = dialog.get_filename()

    dialog.destroy()
    return filename

    #elif response == Gtk.ResponseType.CANCEL:
    #    dialog.destroy()
    #    return -1





