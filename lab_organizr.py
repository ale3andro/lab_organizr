#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import json, sys, os, codecs, paramiko, ntpath, socket, time
    import threading, Queue, datetime, re

    from gi.repository import GObject
    from pcs import *
    from ssh_worker import sshWorker
except ImportError:
    show_warning_window(self.window1, "Κάποια από τις εξαρτήσεις της εφαρμογής δεν έχουν εγκατασταθεί")
    exit(-1)

GObject.threads_init()

class labOrganizr:
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf8')
        self.builder = Gtk.Builder()
        self.builder.add_from_file("assets/lab_organizr_gui.glade")
        self.builder.connect_signals(self)

        self.window1 = self.builder.get_object("window1")
        self.window2 = self.builder.get_object("textEntryDialog_ted")
        self.window3 = self.builder.get_object("textEntryDialog_rf")
        self.window4 = self.builder.get_object("textEntryDialog_receivefiles")
        self.window5 = self.builder.get_object("window_actionProgress")
        self.window1.connect('destroy', lambda w: Gtk.main_quit())

        # Message Log Creation
        self.liststore_log = self.builder.get_object("liststore_log")
        self.treeview_log = self.builder.get_object("treeview_log")
        self.treeview_log_labels = ["Time", "IP", "Type", "Message"]
        for i in range(4):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.treeview_log_labels[i], cell, text=i)
            self.treeview_log.append_column(col)
        self.add_line_to_log("Starting", "begin", "Everything is ok!")

        self.settings = []
        self.actions = []
        json_data = open("assets/settings.json")
        try:
            self.settings = json.load(json_data)
        except:
            show_warning_window(self.window1, "Σφάλμα στο αρχείο ρυθμίσεων.")
            exit(-1)
        json_data.close()

        self.school_classes = self.settings['general']['school_classes'].split(',')
        #Window1 widgets
        self.w1_treeview_columns = ["id", "Όνομα"]

        self.w1_treeview_available_modules = self.builder.get_object("w1_treeview_available_modules")
        self.w1_treeview_available_modules_liststore = Gtk.ListStore(int, str)

        # Populate the actions
        for i in range(2):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.w1_treeview_columns[i], cell, text=i)
            self.w1_treeview_available_modules.append_column(col)
        self.w1_treeview_available_modules.set_model(self.w1_treeview_available_modules_liststore)
        self.w1_treeview_available_modules_liststore.clear()
        for item in self.settings['actions']:
            self.w1_treeview_available_modules_liststore.append([int(item['id']), item['name']])
            self.actions.append(dict(id=item['id'], name=item['name'], file=item['file']))

        self.w1_treeview_selected_modules = self.builder.get_object("w1_treeview_selected_modules")
        self.w1_treeview_selected_modules_liststore = Gtk.ListStore(str, int)
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("´Ονομα", cell, text=0)
        self.w1_treeview_selected_modules.append_column(col)
        self.w1_treeview_selected_modules.set_model(self.w1_treeview_selected_modules_liststore)

        self.w1_treeview_select_pcs = self.builder.get_object("w1_treeview_select_pcs")
        self.w1_treeview_select_pcs_liststore = Gtk.ListStore(str, str)
        for i in range(2):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.w1_treeview_columns[i], cell, text=i)
            self.w1_treeview_select_pcs.append_column(col)
            self.w1_treeview_select_pcs.set_model(self.w1_treeview_select_pcs_liststore)
            self.w1_treeview_select_pcs_liststore.clear()
            for item in self.settings['pcs']:
                self.w1_treeview_select_pcs_liststore.append([item['id'], item['ip']])            
        
        self.w1_button_move_right = self.builder.get_object("w1_button_move_right")
        self.w1_button_move_left = self.builder.get_object("w1_button_move_left")
        self.w1_button_select_pcs_all = self.builder.get_object("w1_button_select_pcs_all")
        self.w1_button_select_pcs_none = self.builder.get_object("w1_button_select_pcs_none")
        # Window 2
        self.w2_entry = self.builder.get_object("ted_entry")
        self.w2_label = self.builder.get_object("ted_label")
        self.w2_combo = self.builder.get_object("ted_combobox")
        self.w2_combo_liststore = self.builder.get_object("liststore_ted_combobox")
        json_data = open("assets/known_processes.json")
        try:
            self.known_processes = json.load(json_data)
        except:
            show_warning_window(self.window1, "Σφάλμα στο αρχείο των γνωστών processes.")
            exit(-1)
        json_data.close()
        for item in self.known_processes['known_processes']:
            self.w2_combo_liststore.append([str(item['app_name']), str(item['process_name'])])
        cell = Gtk.CellRendererText()
        self.w2_combo.pack_start(cell, True)
        self.w2_combo.add_attribute(cell, "text", 0)
        #Window 3
        self.w3_combo = self.builder.get_object("rf_combobox")
        self.w3_radiobutton_online_storage = self.builder.get_object("rf_radiobutton_online_storage")
        self.w3_entry_extension = self.builder.get_object("rf_entry_extension")
        self.w3_combo_liststore = self.builder.get_object("liststore_rf_combobox")
        for item in self.school_classes:
            self.w3_combo_liststore.append([str(item)])
        cell = Gtk.CellRendererText()
        self.w3_combo.pack_start(cell, True)
        self.w3_combo.add_attribute(cell, "text", 0)
        self.w3_combo.set_active(0)
        #Window4
        self.w4_button_ok = self.builder.get_object("receive_files_ok_button")
        self.w4_radiobutton_online_storage = self.builder.get_object("receivefile_radiobutton_online_storage")
        self.w4_radiobutton_offline_storage = self.builder.get_object("receivefile_radiobutton_offline_storage")
        self.w4_combo_classes = self.builder.get_object("receive_files_classes_combobox")
        self.w4_combo_classes_first_run = True
        self.w4_combo_classes_liststore = self.builder.get_object("receive_files_classes_liststore")
        self.w4_combo_dates = self.builder.get_object("receive_files_dates_combobox")
        self.w4_combo_dates_liststore = self.builder.get_object("receive_files_dates_liststore")
        for item in self.school_classes:
            self.w4_combo_classes_liststore.append([str(item)])
        cell = Gtk.CellRendererText()
        self.w4_combo_classes.pack_start(cell, True)
        self.w4_combo_classes.add_attribute(cell, "text", 0)
        self.w4_combo_classes.set_active(0)
        cell = Gtk.CellRendererText()
        self.w4_combo_dates.pack_start(cell, True)
        self.w4_combo_dates.add_attribute(cell, "text", 0)
        # Window 5
        self.w5_button_close = self.builder.get_object("actionProgress_close_button")
        self.w5_treeview = self.builder.get_object("actions_progress_treeview")
        self.w5_treeview_liststore = self.builder.get_object("action_progress_liststore")
        self.w5_treeview_columns = ["ip", "result"]
        for i in range(2):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.w5_treeview_columns[i], cell, text=i)
            self.w5_treeview.append_column(col)
        self.w5_treeview_liststore.clear()


        # Μεταβλητές που θα χρειαστούν για την ssh σύνδεση
        self.selectedPcs = {}
        self.selectedActions = []
        self.onlineStorage = True
        self.window1.show_all()

    def on_w1_button_clear_log_clicked(self, *args):
        self.liststore_log.clear()

    def on_w1_button_move_left_clicked(self, *args):
        if (len(self.w1_treeview_selected_modules_liststore)==0):
            return
        selection = self.w1_treeview_selected_modules.get_selection().get_selected()
        if (selection[1]!=None):
            self.w1_treeview_selected_modules_liststore.remove(selection[1])

    def on_w1_button_move_right_clicked(self, *args):
        selection = self.w1_treeview_available_modules.get_selection().get_selected()
        if (selection[1]!=None):
            item = [selection[0].get_value(selection[1],1), selection[0].get_value(selection[1],0)]
            self.w1_treeview_selected_modules_liststore.append(item)
        
    def on_w1_button_select_pcs_all_clicked(self, *args):
        self.w1_treeview_select_pcs.get_selection().select_all()
    
    def on_w1_button_select_pcs_none_clicked(self, *args):
        self.w1_treeview_select_pcs.get_selection().unselect_all()

    def on_w1_button_clear_actions_clicked(self, *args):
        if (len(self.w1_treeview_selected_modules_liststore)!=0):
            self.w1_treeview_selected_modules_liststore.clear()

    def on_w1_button_exit_clicked(self, *args):
        Gtk.main_quit()

    def on_w1_button_execute_clicked(self, *args):
        # Πρώτα έλεγχος για το ποιά pcs επιλέχθηκαν
        (model, pathlist) = self.w1_treeview_select_pcs.get_selection().get_selected_rows()
        if (len(pathlist)==0):
            show_warning_window(self.window1, "Πρέπει να επιλέξεις PCs!")
            return
        self.selectedPcs = {}
        self.selectedActions[:] = []
        for item in pathlist:
            self.selectedPcs[model[item][0]] = self.getPCDetailsFromIP(model[item][1])

        # Μετά έλεγχος για το ποιό action επιλέχθηκε
        if (len(self.w1_treeview_selected_modules_liststore)==0):
            show_warning_window(self.window1, "Πρέπει να επιλέξεις ενέργεια!")
            return
        else:
            for item in self.w1_treeview_selected_modules_liststore:
                self.selectedActions.append(item[1])
                print item[0], item[1]
        self.makeConnections()

    def getClientDetailsFromClassId(self, classId):
        for item in self.settings['client_classes']:
            if item['id']==classId:
                return { "label" : item['label'] , "desktop_folder_name" : item['desktop_folder_name'] }

    def getPCDetailsFromIP(self, ip):
        for item in self.settings['pcs']:
            if item['ip']==str(ip):
                client_details = self.getClientDetailsFromClassId(item['client_class'])
                return {"id": item['id'],
                            "ip":ip,
                            "username":item['username'],
                            "password":item['password'],
                            "super_username":item['super_username'],
                            "super_password":item['super_password'],
                            "client_class_label" : client_details["label"],
                            "desktop_folder_name" : client_details["desktop_folder_name"]
                }

    def getFilenameFromActionId(self, actionId):
        for item in self.actions:
            if item['id']==str(actionId):
                return item['file']
        return -1

    def createSSHClient(self, server, port, user, password):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, port, user, password)
        return client

    def show_rf_entry_dialog(self):
        self.w3_radiobutton_online_storage.set_active(True)
        self.w3_entry_extension.set_text("*")
        if self.window3.run() == 1:
            self.window3.hide()
            index = self.w3_combo.get_active()
            model = self.w3_combo.get_model()
            self.onlineStorage = self.w3_radiobutton_online_storage.get_active()
            return (model[index][0], re.sub('[*.]', '', self.w3_entry_extension.get_text()))
        self.window3.hide()
        return -1

    def show_return_files_entry_dialog(self):
        self.w4_radiobutton_online_storage.set_active(True)
        self.w4_button_ok.set_sensitive(False)
        if self.window4.run() == 1:
            index = self.w4_combo_classes.get_active()
            model = self.w4_combo_classes.get_model()
            selectedClass = model[index][0]
            index = self.w4_combo_dates.get_active()
            model = self.w4_combo_dates.get_model()
            selectedDate = model[index][0]
            self.window4.hide()
            return (selectedClass, selectedDate)
        else:
            self.window4.hide()
            return (-1, -1)

    def updateW4(self):
        self.w4_combo_dates_liststore.clear()
        index = self.w4_combo_classes.get_active()
        model = self.w4_combo_classes.get_model()
        selectedClass = model[index][0]
        if (self.onlineStorage):
            storageDir = self.settings['general']['online_save_folder'] + selectedClass + "/"
        else:
            storageDir = self.settings['general']['offline_save_folder'] + selectedClass + "/"
        try:
            allItems = []
            for item in os.listdir(storageDir):
                if os.path.isdir(storageDir + item):
                    #self.w4_combo_dates_liststore.append([str(item)])
                    #self.w4_combo_dates.set_active(0)
                    allItems.append(item)
            allItems.sort()
            for item in allItems:
                self.w4_combo_dates_liststore.append([str(item)])
                self.w4_combo_dates.set_active(0)
            self.w4_button_ok.set_sensitive(True)
        except OSError:
            self.w4_button_ok.set_sensitive(False)

    def on_receive_files_classes_combobox_changed(self, *args):
        if (self.w4_combo_classes_first_run):
            self.w4_combo_classes_first_run = False
        else:
            self.updateW4()

    def on_receivefile_radiobutton_online_storage_toggled(self, *args):
        self.onlineStorage = self.w4_radiobutton_online_storage.get_active()
        index = self.w4_combo_classes.get_active()
        model = self.w4_combo_classes.get_model()
        selectedClass = model[index][0]
        self.updateW4()

    def show_text_entry_dialog(self, msg="Όνομα εφαρμογής"):
        self.w2_entry.set_text("")
        self.w2_label.set_text(msg)
        if self.window2.run() == 1:
            self.window2.hide()
            if (self.w2_entry.get_text()!=""):
                return self.w2_entry.get_text()
            else:
                index = self.w2_combo.get_active()
                model = self.w2_combo.get_model()
                item = model[index]
                return item[1]
        self.window2.hide()
        return -1

    def add_line_to_log(self, theHostname, theType, theMsg):
        theTime = time.strftime('%H:%M:%S', time.localtime(time.time()))
        self.liststore_log.append([str(theTime), theHostname, theType, theMsg])

    def get_date(self):
        return datetime.date.today()

    def on_actionProgress_close_button_clicked(self, *args):
        self.window5.hide()

    def list_remote_files(self, theHostname, theUsername, thePassword, dirName):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        outFiles = []
        try:
            ssh.connect(hostname=theHostname, username=theUsername, password=thePassword, timeout=5)
        except socket.error:
            self.add_line_to_log(str(theHostname), str("ssh::socket_error"), "Αδυναμία σύνδεσης.")
        try:
            aCommand = "cd " + dirName + " && find . -maxdepth 1 -type f -printf '%f\n'"
            print aCommand
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(aCommand)
            for line in ssh_stdout.read().splitlines():
                outFiles.append(line)
            for line in ssh_stderr.read().splitlines():
                print "ERROR:" + line
        except paramiko.SSHException:
            self.add_line_to_log(str(theHostname), str("ssh::paramiko.SSHException"), "Channel closed.")
        return outFiles

    def run_ssh_command(self, theHostname, theUsername, thePassword, command):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=theHostname, username=theUsername, password=thePassword, timeout=5)
        except socket.error:
            self.add_line_to_log(str(theHostname), str("ssh::socket_error"), "Αδυναμία σύνδεσης.")

        try:
            print theHostname, command
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command.encode('utf-8'))
            for line in ssh_stdout.read().splitlines():
                self.add_line_to_log(str(theHostname), str("ssh::responce"), line)
            countLines=0
            for line in ssh_stderr.read().splitlines():
                self.add_line_to_log(str(theHostname), str("ssh::error"), line)
                countLines+=1
            if (countLines==0):
                self.add_line_to_log(str(theHostname), str("ssh::success"), "Success: " + command.encode('utf-8'))
        except paramiko.SSHException:
            self.add_line_to_log(str(theHostname), str("ssh::paramiko.SSHException"), "Channel closed.")

    def makeConnections(self):
       for item in self.selectedActions:
            if (self.getFilenameFromActionId(item)!=-1):
                filename = os.path.dirname(os.path.realpath(__file__)) + "/assets/" + self.getFilenameFromActionId(item)
            if (os.path.isfile(filename)):
                json_data = codecs.open(filename, "r", "utf-8")
                try:
                    actionSettings = json.load(json_data)
                except:
                    show_warning_window(self.window1, "Σφάλμα στο αρχείο ρυθμίσεων του action!")
                    exit(-1)
                json_data.close()

                # Διάβασμα ρυθμίσεων του action
                command = actionSettings["command"]
                asRoot = actionSettings["asRoot"]
                actionArguments = actionSettings["arguments"]
                actionType = "not defined"

                fArgs={}
                for argument in actionArguments:
                    if (argument["id"]=="0"):
                        actionType = argument["type"]
                    elif (argument["type"]=="textBox"):
                        fArgs[int(argument['id'])] = self.show_text_entry_dialog("Όνομα εφαρμογής")
                        if fArgs[int(argument['id'])]==-1:
                            return
                    elif (argument["type"]=="fileChooser"):
                        fArgs[int(argument["id"])] = show_file_chooser(self.window1, "Διάλεξε αρχείο")
                        if fArgs[int(argument['id'])] == -1:
                            return
                    elif (argument["type"] == "directoryChooser"):
                        fArgs[int(argument["id"])] = show_directory_chooser(self.window1, "Διάλεξε αρχείο")
                        if fArgs[int(argument['id'])] == -1:
                            return

                if (actionType == "put"):
                    put_scpFile = show_file_chooser(self.window1, "Διάλεξε αρχείο για αποστολή")
                    if (put_scpFile == "-1"):
                        print "action aborted"
                        return
                if (actionType == "get"):
                    school_class, extension = self.show_rf_entry_dialog()
                    if school_class==-1:
                        return

                if (actionType == "return"):
                    return_school_class, return_date = self.show_return_files_entry_dialog()
                    if (return_school_class==-1 or return_date ==-1):
                        return

                queue = Queue.Queue()
                self.w5_treeview_liststore.clear()
                for item in self.selectedPcs:
                    self.w5_treeview_liststore.append([self.selectedPcs[item]['ip'], 'Σε αναμονή...'])
                self.window5.show_all()
                for item in self.selectedPcs:
                    hostname = self.selectedPcs[item]['ip']
                    friendlyname = self.selectedPcs[item]['id']
                    desktopFolderName = self.selectedPcs[item]['desktop_folder_name']
                    if asRoot == "1":
                        username = self.selectedPcs[item]['super_username']
                        password = self.selectedPcs[item]['super_password']
                    else:
                        username = self.selectedPcs[item]['username']
                        password = self.selectedPcs[item]['password']
                    execute = True
                    if (execute):
                        if (actionType == "get"):
                            sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                            sshThread.daemon = True
                            sshThread.start()
                            origin = "/home/" + username + "/" + desktopFolderName + "/"
                            origin.encode("utf-8")
                            if self.onlineStorage:
                                destination = self.settings['general']['online_save_folder'] + school_class + "/" + str(self.get_date()) + "/" + friendlyname + "/"
                            else:
                                destination = self.settings['general']['offline_save_folder'] + school_class + "/" + str(self.get_date()) + "/" + friendlyname + "/"
                            destination.encode('utf-8')
                            queue.put(('get', hostname, username, password, origin, destination, extension))
                        elif (actionType == "put"):
                            sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                            sshThread.daemon = True
                            sshThread.start()
                            destination = "/home/" + username + "/" + desktopFolderName + "/" + ntpath.basename((put_scpFile))
                            destination.encode('utf-8')
                            queue.put(('put', hostname, username, password, destination, put_scpFile))
                        elif (actionType == "return"):
                            sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                            sshThread.daemon = True
                            sshThread.start()
                            destination = "/home/" + username + "/" + desktopFolderName + "/"
                            destination.encode('utf-8')
                            if self.onlineStorage:
                                origin = self.settings['general']['online_save_folder']
                            else:
                                origin = self.settings['general']['offline_save_folder']
                            origin = origin + str(return_school_class) + "/" + str(return_date) + "/" + str(friendlyname) + "/"
                            origin = origin.encode('utf-8')
                            queue.put(('return', hostname, username, password, origin, destination))
                        else:
                            sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                            sshThread.daemon = True
                            sshThread.start()
                            if (command.count('$')!=0):
                                if (len(fArgs) != command.count('$')):
                                    print "Error. Mismatch in number of argument"
                                    add_line_to_log(self, hostname, "ssh", "Λάθος αριθμός ορισμάτων")
                                    return
                                for i in range(1, len(fArgs) + 1):
                                    command = command.replace("$" + str(i), fArgs[i])
                            queue.put(('ssh', hostname, username, password, command))
                    else:
                        print "Passed ssh phase w/o connections!"
                #queue.join()
            else:
                print filename, ' does not exist!'
                return



    def exit_application(self, *args):
        Gtk.main_quit(*args)

if __name__ == "__main__":
    main = labOrganizr()
    Gtk.main()
