#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading, Queue, paramiko, socket, os, time

class sshWorker(threading.Thread):
    def __init__(self, queue, name, liststore_log, liststore_action_progress):
        threading.Thread.__init__(self)
        self.queue = queue
        self.name = name
        self.liststore_log = liststore_log
        self.liststore_action_progress = liststore_action_progress

    def get_time(self):
        return str(time.strftime('%H:%M:%S', time.localtime(time.time())))

    def list_local_files(self, dirName):
        return 0

    def modify_line_to_action_progress_log(self, theFriendlyName, theMsg):
        for item in self.liststore_action_progress:
            if item[0] == theFriendlyName:
                item[1] = theMsg

    def list_remote_files(self, theHostname, theUsername, thePassword, dirName, extension):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        outFiles = []
        try:
            ssh.connect(hostname=theHostname, username=theUsername, password=thePassword, timeout=5)
        except socket.error:
            self.liststore_log.append([self.get_time(), str(theHostname), "thread-list_remote_files-1", "Αδυναμία σύνδεσης."])
        try:
            if (extension==""):
                aCommand = "cd " + dirName.replace(" ", "\ ") + " && find . -maxdepth 1 -type f -printf '%f\\n'"
            else:
                aCommand = "cd " + dirName.replace(" ", "\ ") + " && find . -maxdepth 1 -type f -name '*." + extension + "' -printf '%f\\n'"
            print aCommand
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(aCommand.encode('utf-8'))
            for line in ssh_stdout.read().splitlines():
                outFiles.append(line)
            for line in ssh_stderr.read().splitlines():
                print line
                self.liststore_log.append([self.get_time(), str(theHostname), "thread-list_remote_files-2", "Σφάλμα λίστας αρχείων"])
        except paramiko.SSHException:
            self.liststore_log.append([self.get_time(), str(theHostname), "thread-list_remote_files-3", "SSH Exception."])
        return outFiles

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            details = self.queue.get()
            hostname = details[1]
            username = details[2]
            password = details[3]
            if (details[0]=="put"):
                destination = details[4]
                put_scpFile = details[5]
                try:
                    t = paramiko.Transport((hostname, 22))
                    t.set_keepalive(5)
                    t.connect(username=username, password=password)
                    sftp = paramiko.SFTPClient.from_transport(t)
                    sftp.put(put_scpFile, destination)
                    self.liststore_log.append([self.get_time(), hostname, "put", "Επιτυχής αποστολή αρχείων."])
                    self.modify_line_to_action_progress_log(hostname, "Ok")
                except paramiko.SSHException as e:
                    self.liststore_log.append([self.get_time(), hostname, "put", "Αδυναμία σύνδεσης ssh_put"])
                    self.modify_line_to_action_progress_log(hostname, "Αδυναμία σύνδεσης ssh")
                    print e
                self.queue.task_done()
            elif (details[0]=="get"):
                origin = details[4]
                destination = details[5]
                extension = details[6]
                try:
                    t = paramiko.Transport((hostname, 22))
                    t.set_keepalive(5)
                    t.connect(username=username, password=password)
                    sftp = paramiko.SFTPClient.from_transport(t)
                    files2Get = self.list_remote_files(hostname, username, password, origin, extension)
                    if (len(files2Get)==0):
                        self.liststore_log.append([self.get_time(), hostname, "get", "Δεν υπάρχουν αρχεία στον φάκελο"])
                        self.modify_line_to_action_progress_log(hostname, "Δεν υπάρχουν αρχεία στον φάκελο")
                    else:
                        for file in files2Get:
                            print file + ":"
                            if not os.path.exists(destination):
                                os.makedirs(destination)
                            sftp.get(origin + file, destination + file)
                        self.liststore_log.append([self.get_time(), hostname, "get", "Επιτυχής λήψη αρχείων."])
                        self.modify_line_to_action_progress_log(hostname, "Ok")
                except paramiko.SSHException:
                    self.liststore_log.append([self.get_time(), hostname, "get", "Αδυναμία σύνδεσης ssh_get"])
                    self.modify_line_to_action_progress_log(hostname, "Αδυναμία σύνδεσης ssh")
                self.queue.task_done()
            elif (details[0]=="return"):
                origin = details[4]
                destination = details[5]
                try:
                    t = paramiko.Transport((hostname, 22))
                    t.set_keepalive(5)
                    t.connect(username=username, password=password)
                    sftp = paramiko.SFTPClient.from_transport(t)
                    if not os.path.isdir(origin):
                        self.liststore_log.append([self.get_time(), hostname, "return", "Δεν υπάρχει φάκελος για τον υπολογιστή"])
                        self.modify_line_to_action_progress_log(hostname, "Δεν υπάρχει φάκελος για τον υπολογιστή")
                        return
                    if (len(os.listdir(origin)) == 0):
                        self.liststore_log.append([self.get_time(), hostname, "return", "Δεν υπάρχουν αρχεία για επιστροφή στο φάκελο"])
                        self.modify_line_to_action_progress_log(hostname, "Δεν υπάρχουν αρχεία για επιστροφή στο φάκελο")
                    else:
                        for item in os.listdir(origin):
                            sftp.put(origin+item, destination+item)
                        self.liststore_log.append([self.get_time(), hostname, "return", "Επιτυχής αποστολή αρχείων."])
                        self.modify_line_to_action_progress_log(hostname, "Ok")
                except paramiko.SSHException:
                    self.liststore_log.append([self.get_time(), hostname, "return", "Αδυναμία σύνδεσης ssh_return"])
                    self.modify_line_to_action_progress_log(hostname, "Αδυναμία σύνδεσης ssh")
                self.queue.task_done()
            elif (details[0]=="ssh"):
                command = details[4]
                ssh = paramiko.SSHClient()
                ssh.load_system_host_keys()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    ssh.connect(hostname=hostname, username=username, password=password, timeout=5)
                    try:
                        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command.encode('utf-8'))
                        for line in ssh_stdout.read().splitlines():
                            self.liststore_log.append([self.get_time(), hostname, "ssh-responce", line])
                        countLines = 0
                        for line in ssh_stderr.read().splitlines():
                            self.liststore_log.append([self.get_time(), hostname, "ssh-error", line])
                            countLines += 1
                        if (countLines == 0):
                            self.liststore_log.append([self.get_time(), hostname, "ssh", "Επιτυχής εκτέλεση εντολής:" + command.encode('utf-8')])
                            self.modify_line_to_action_progress_log(hostname, "Ok")
                    except paramiko.SSHException:
                        self.liststore_log.append(
                            [self.get_time(), hostname, "ssh-error", "Αποτυχία εκτέλεση εντολής:" + command.encode('utf-8')])
                        self.modify_line_to_action_progress_log(hostname, "Αδυναμία σύνδεσης ssh - ssh exception")
                except socket.error:
                    self.liststore_log.append([self.get_time(), hostname, "ssh", "Αδυναμία σύνδεσης ssh"])
                    self.modify_line_to_action_progress_log(hostname, "Αδυναμία σύνδεσης ssh")
                self.queue.task_done()