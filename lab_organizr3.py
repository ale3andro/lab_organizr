#!/usr/bin/python3
# -*- coding: utf-8 -*-

try:
    import json, sys, os, codecs, paramiko, ntpath, socket, time
    import threading, queue, datetime, logging, re, glob
    from importlib import reload

    from gi.repository import GObject, GLib
    from pcs import *
    from ssh_worker import sshWorker
except ImportError:
    show_warning_window(self.window1, "Κάποια από τις εξαρτήσεις της εφαρμογής δεν έχουν εγκατασταθεί")
    exit(-1)

GObject.threads_init()

class labOrganizr:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not os.path.exists("log"):
            os.makedirs("log")
        handler = logging.FileHandler('log/app.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Εκκίνηση εφαρμογής')

        reload(sys)
        #sys.setdefaultencoding('utf8')
        self.builder = Gtk.Builder()
        try:
            self.builder.add_from_file("assets/lab_organizr_gui.glade")
        except GLib.Error:
            dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK)
            dialog.set_markup("Δεν βρέθηκε το glade αρχείο που περιέχει το GUI - διαδρομή assets/lab_organizr_gui.glade")
            if (dialog.run() == Gtk.ResponseType.OK):
                dialog.destroy()
            self.logger.error("Δεν βρέθηκε το glade αρχείο που περιέχει το GUI - διαδρομή assets/lab_organizr_gui.glade")
            exit(-1)

        self.builder.connect_signals(self)

        self.window1 = self.builder.get_object("window1")
        self.window2 = self.builder.get_object("textEntryDialog_ted")
        self.window3 = self.builder.get_object("textEntryDialog_rf")
        self.window4 = self.builder.get_object("textEntryDialog_receivefiles")
        self.window5 = self.builder.get_object("window_actionProgress")
        self.window6 = self.builder.get_object("simpleTextBox_stb")
        self.window1.connect('destroy', lambda w: Gtk.main_quit())

        # Message Log Creation
        self.liststore_log = self.builder.get_object("liststore_log")
        self.treeview_log = self.builder.get_object("treeview_log")
        self.treeview_log_labels = ["Time", "IP", "Type", "Message"]
        for i in range(4):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.treeview_log_labels[i], cell, text=i)
            self.treeview_log.append_column(col)
        self.add_line_to_log("...", "...", "Εκκίνηση χωρίς σφάλματα")
        self.version = os.popen("git log -1").read()
        for line in self.version.split('\n'):
            if (line!=""):
                self.add_line_to_log("git", "log", line)

        self.number_of_selected_actions = 0
        self.number_of_current_action_to_be_executed = 0
        self.settings = []
        self.actions = []
        try:
            json_data = open("assets/settings.json")
            self.settings = json.load(json_data)
        except IOError as e:
            show_warning_window(self.window1, "Δεν βρέθηκε το αρχείο ρυθμίσεων")
            self.logger.error("Δεν βρέθηκε το αρχείο ρυθμίσεων - διαδρομή assets/settings.json")
            exit(-1)
        except:
            show_warning_window(self.window1, "Σφάλμα μορφής στο αρχείο ρυθμίσεων.")
            self.logger.error("Το json αρχείο ρυθμίσεων δεν είναι έγκυρο - διαδρομή assets/settings.json")
            exit(-1)
        json_data.close()

        self.school_classes = self.settings['general']['school_classes'].split(',')
        #Window1 widgets
        self.w1_treeview_columns = ["id", "Όνομα"]

        self.w1_treeview_available_modules = self.builder.get_object("w1_treeview_available_modules")
        self.w1_treeview_available_modules_liststore = Gtk.ListStore(int, str)

        actionFiles = sorted(glob.glob(os.getcwd()+"/assets/scripts/script_*"))
        self.allActions = []
        counter=0
        for i in actionFiles:
            actionSettings = json.load(open(i))
            if 'enabled' in actionSettings:
                if (actionSettings['enabled']=="True"):
                    self.allActions.append(dict(id=counter, name=actionSettings['name'], file=i))
                    self.add_line_to_log("init", "...", "Το action " + i + " ενεργοποιήθηκε")
                    counter+=1
            else:
                self.logger.error("Το action " + i + " δεν ενεργοποιήθηκε")
                self.add_line_to_log("init", "...", "Το action " + i + " δεν ενεργοποιήθηκε")

        # Populate the actions
        for i in range(2):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.w1_treeview_columns[i], cell, text=i)
            self.w1_treeview_available_modules.append_column(col)
        self.w1_treeview_available_modules.set_model(self.w1_treeview_available_modules_liststore)
        self.w1_treeview_available_modules_liststore.clear()
        for item in self.allActions:
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
        try:
            json_data = open("assets/known_processes.json")
            self.known_processes = json.load(json_data)
        except IOError:
            show_warning_window(self.window1, "Αδυναμία εντοπισμού αρχείου γνωστών processes")
            self.logger.error("Αδυναμία εντοπισμού αρχείου γνωστών processes - διαδρομή assets/known_processes.json")
            exit(-1)
        except:
            show_warning_window(self.window1, "Σφάλμα μορφοποίησης στο αρχείο των γνωστών processes.")
            self.logger.error("Το json αρχείο των γνωστών processes δεν είναι έγκυρο - διαδρομή assets/known_processes.json")
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
        self.w5_button_next_action = self.builder.get_object("nextAction_button")
        self.w5_button_next_action.set_sensitive(False)
        self.w5_label_action_executed_now = self.builder.get_object("current_action_label")
        self.w5_treeview = self.builder.get_object("actions_progress_treeview")
        self.w5_treeview_liststore = self.builder.get_object("action_progress_liststore")
        self.w5_treeview_columns = ["ip", "result"]
        for i in range(2):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(self.w5_treeview_columns[i], cell, text=i)
            self.w5_treeview.append_column(col)
        self.w5_treeview_liststore.clear()
        # Window 6
        self.w6_label = self.builder.get_object("stb_label")
        self.w6_text = self.builder.get_object("stb_text")

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
        self.logger.info('Τερματισμός εφαρμογής')
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
        self.number_of_selected_actions=len(self.selectedActions)
        self.number_of_current_action_to_be_executed=0
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
                            "desktop_folder_name" : client_details["desktop_folder_name"],
                            "client_class" : item['client_class']
                }

    def getFilenameFromActionId(self, actionId):
        for item in self.actions:
            if item['id']==actionId:
                return item['file']
        return -1

    def createSSHClient(self, server, port, user, password):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, port, user, password)
        return client

    def show_rf_entry_dialog(self, defaultExtension="*"):
        self.w3_radiobutton_online_storage.set_active(True)
        if (defaultExtension=="*"):
            self.w3_entry_extension.set_text("*")
        else:
            self.w3_entry_extension.set_text(defaultExtension)
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
            self.logger.warn("Συνάρτηση updateW4, αδυναμία δημιουργίας λίστας αρχείων φακέλου.")
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

    def show_simple_text_entry_dialog(self, msg="Τιμή;"):
        self.w6_label.set_text(msg)
        if self.window6.run() == 1:
            self.window6.hide()
            if (self.w6_text.get_text()!=""):
                return self.w6_text.get_text()
            else:
                return -1
        self.window6.hide()

    def add_line_to_log(self, theHostname, theType, theMsg):
        theTime = time.strftime('%H:%M:%S', time.localtime(time.time()))
        self.liststore_log.append([str(theTime), theHostname, theType, theMsg])

    def get_date(self):
        return datetime.date.today()

    def on_actionProgress_close_button_clicked(self, *args):
        self.window5.hide()

    def on_nextAction_button_clicked(self, *args):
        self.makeConnections()

    def makeConnections(self):
        item = self.selectedActions[self.number_of_current_action_to_be_executed]
        if (self.getFilenameFromActionId(item)!=-1):
            filename = os.path.dirname(os.path.realpath(__file__)) + "/assets/" + self.getFilenameFromActionId(item)
            filename = self.getFilenameFromActionId(item)
        else:
            show_warning_window(self.window1, "Αδυναμία εντοπισμού αρχείου action από το id του")
            self.logger.error("Αδυναμία εντοπισμού αρχείου action από το id του")
            return

        if (os.path.isfile(filename)):
            json_data = codecs.open(filename, "r", "utf-8")
            try:
                actionSettings = json.load(json_data)
            except:
                show_warning_window(self.window1, "Σφάλμα στο αρχείο ρυθμίσεων του action!")
                exit(-1)
            json_data.close()

            # Διάβασμα ρυθμίσεων του action
            actionName = actionSettings["name"]
            actionType = actionSettings["actionType"]
            asRoot = actionSettings["asRoot"]
            actionArguments = actionSettings["arguments"]
            command = actionSettings["command"]
            originFolder = ""
            displayOnly = False

            fArgs={}
            if (actionType == "custom"):
                if (len(actionArguments)>0):
                    for argument in actionArguments:
                        if (argument["type"]=="instanceBox"):
                            fArgs[int(argument['num'])] = self.show_text_entry_dialog(argument['prompt'])
                            if fArgs[int(argument['num'])]==-1:
                                return
                        elif (argument["type"]=="textBox"):
                            fArgs[int(argument['num'])] = self.show_simple_text_entry_dialog(argument['prompt'])
                            if fArgs[int(argument['num'])]==-1:
                                return
                        elif (argument["type"]=="fileChooser"):
                            fArgs[int(argument["num"])] = show_file_chooser(self.window1, "Διάλεξε αρχείο", self.settings['general']['online_save_folder'])
                            if fArgs[int(argument['num'])] == -1:
                                return
                        elif (argument["type"] == "directoryChooser"):
                            fArgs[int(argument["num"])] = show_directory_chooser(self.window1, "Διάλεξε αρχείο")
                            if fArgs[int(argument['num'])] == -1:
                                return
                        else:
                            exit("Δεν υποστηρίζεται το όρισμα")
                    # Δημιουργία του Command - TODO εδώ να μπει έλεγχος σε περίπτωση που δεν καλύπτονται όλα τα ορίσματα`
                    for key,value in fArgs.iteritems():
                        command = command.replace("%" + str(key), value)
            if (actionType == "put"):
                #put_scpFolder = show_directory_chooser(self.window1, "Διάλεξε φάκελο για αποστολή", self.settings['general']['online_save_folder'])
                #print(put_scpFolder)
                #exit(1)
                put_scpFiles = show_file_chooser(self.window1, "Διάλεξε αρχείο για αποστολή", self.settings['general']['online_save_folder'])
                if (put_scpFiles == "-1"):
                    print("action aborted")
                    return
            if (actionType == "get"):
                defaultExtension="*"
                if (len(actionArguments)>0):
                    for argument in actionArguments:
                        if (argument["type"]=="defaultExtension"):
                            defaultExtension=argument["extension"]
                        if (argument["type"]=="listOnly"):
                            displayOnly = True
                if (not displayOnly):
                    school_class, extension = self.show_rf_entry_dialog(defaultExtension)
                    if school_class==-1:
                        return
                    if (len(actionArguments)>0):
                        for argument in actionArguments:
                            if (argument["type"]=="originFolder"):
                                originFolder = argument["directory"]
                else:
                    school_class="-"
                    extension="*"
            if (actionType == "return"):
                return_school_class, return_date = self.show_return_files_entry_dialog()
                if (return_school_class==-1 or return_date ==-1):
                    return

            queue = Queue.Queue()
            self.w5_treeview_liststore.clear()
            for item in self.selectedPcs:
                self.w5_treeview_liststore.append([self.selectedPcs[item]['ip'], 'Σε αναμονή...'])
            self.w5_button_next_action.set_sensitive(not (self.number_of_current_action_to_be_executed+1)==self.number_of_selected_actions)
            self.w5_label_action_executed_now.set_text("Ενέργεια: " + str(self.number_of_current_action_to_be_executed) + ": " + actionName)
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
                    if (actionType == "custom"):
                        sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                        sshThread.daemon = True
                        sshThread.start()
                        # TODO πάρε από εδώ τον έλεγχο και βάλτο μέσα στο main κατασκευή command
                        if (command.count('%')!=0):
                            if (len(fArgs) != command.count('%')):
                                print("Error. Mismatch in number of argument")
                                add_line_to_log(self, hostname, "ssh", "Λάθος αριθμός ορισμάτων")
                                return
                            for i in range(1, len(fArgs) + 1):
                                command = command.replace("%" + str(i), fArgs[i])
                        queue.put(('custom', hostname, username, password, command))
                    elif (actionType == "get"):
                        sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                        sshThread.daemon = True
                        sshThread.start()
                        if (originFolder == ""):
                            origin = "/home/" + username + "/" + desktopFolderName + "/"
                        else:
                            origin = originFolder
                        origin.encode("utf-8")
                        if self.onlineStorage:
                            destination = self.settings['general']['online_save_folder'] + school_class + "/" + str(self.get_date()) + "/" + friendlyname + "/"
                        else:
                            destination = self.settings['general']['offline_save_folder'] + school_class + "/" + str(self.get_date()) + "/" + friendlyname + "/"
                        destination.encode('utf-8')
                        queue.put(('get', hostname, username, password, origin, destination, extension, displayOnly))
                    elif (actionType == "put"):
                        sshThread = sshWorker(queue, friendlyname, self.liststore_log, self.w5_treeview_liststore)
                        sshThread.daemon = True
                        sshThread.start()
                        destination = "/home/" + username + "/" + desktopFolderName + "/"
                        destination.encode("utf-8")
                        queue.put(('put', hostname, username, password, destination, put_scpFiles))
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
                        if (command.count('%')!=0):
                            if (len(fArgs) != command.count('%')):
                                print("Error. Mismatch in number of argument")
                                add_line_to_log(self, hostname, "ssh", "Λάθος αριθμός ορισμάτων")
                                return
                            for i in range(1, len(fArgs) + 1):
                                command = command.replace("%" + str(i), fArgs[i])
                        queue.put(('ssh', hostname, username, password, command))
                else:
                    print("Passed ssh phase w/o connections!")
        else:
            print(filename, ' does not exist!')
            return
        self.number_of_current_action_to_be_executed+=1
        #if (not self.number_of_current_action_to_be_executed==self.number_of_selected_actions):
        #    print('more actions pending')

    def exit_application(self, *args):
        Gtk.main_quit(*args)
    
    

if __name__ == "__main__":
    main = labOrganizr()
    Gtk.main()
