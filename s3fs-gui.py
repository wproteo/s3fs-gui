#!/usr/bin/python
# -*- coding: utf-8 -*-
import gi
import os
import subprocess
import sqlite3
import json
import locale

from os import path
from threading import Timer

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

# CONFIG
# Mount point is a subfoldser of $HOME user
mountFolder = "mnt"
# Default language if the translation does not exist
default_lang = "en"

# Mount point is a subfoldser of $HOME user
mountPoint = os.path.join(os.environ['HOME'], mountFolder)
builder = Gtk.Builder()
conn = sqlite3.connect('res/db.sqlite')
cursor = conn.cursor()
select_bucket = ""
lang = ""

def main():
    """Load user interface and language"""
    global lang
    global select_bucket
    lang = json.loads(get_language())
    if not path.exists(mountPoint):
        os.mkdir(mountPoint)

    builder.add_from_file("res/gui.glade")
    builder.connect_signals(Handler())
    select_bucket = builder.get_object("select_bucket")
    set_labels()
    create_select_bucket()

    window = builder.get_object("window1")

    window.connect("delete-event", Gtk.main_quit)
    window.show_all()
    Gtk.main()

class Handler:
    """Class to interact with the user interface"""
    def on_mount_clicked(self, button):
        """Mount button click"""
        global select_bucket
        bucket = int(select_bucket.get_active_id())

        if bucket > 0:
            cursor.execute("SELECT * FROM buckets WHERE id = ? ",(bucket,))
            row = cursor.fetchone()

            mountBucketPoint = os.path.join(mountPoint, row[1])
            if not path.exists(mountBucketPoint):
                os.mkdir(mountBucketPoint)

            filename = os.path.join(os.environ['HOME'], "."+row[1]+"-s3fs")

            subprocess.Popen("echo "+row[3]+":"+row[4]+" > ${HOME}/."+row[1]+"-s3fs", stdout=subprocess.PIPE, shell=True)
            subprocess.Popen("chmod 600 ${HOME}/."+row[1]+"-s3fs", stdout=subprocess.PIPE, shell=True)

            command = "s3fs "+row[1]+" "+mountBucketPoint+" -o passwd_file="+filename+" -o url="+row[2]+" -o use_path_request_style -o use_cache=/tmp"
            #print(command)
            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            p_status = p.wait()
            if p_status == 0:
                status_msg =  lang["msg_mounted"]
            else:
                status_msg = output
        else:
            status_msg = lang["msg_no_selection"]

        set_status(status_msg)
        print(status_msg)

    def on_unmount_clicked(self, button):
        global select_bucket
        bucket = int(select_bucket.get_active_id())

        if bucket > 0:
            filename = os.path.join(os.environ['HOME'], "."+select_bucket.get_active_text()+"-s3fs")
            #print(filename)

            mountBucketPoint = os.path.join(mountPoint, select_bucket.get_active_text())
            p = subprocess.Popen("fusermount -u "+mountBucketPoint, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            p_status = p.wait()
            if p_status == 0:
                status_msg =  lang["msg_unmounted"]
            else:
                status_msg = output

            set_status(status_msg)
            print(status_msg)

            if os.path.exists(filename):
                os.remove(filename)

    def on_select_bucket_changed(self, select_bucket):
        builder.get_object("host").set_text("")
        builder.get_object("key").set_text("")
        builder.get_object("secret").set_text("")
        builder.get_object("bucket").set_text("")

    def on_edit_clicked(self, button):
        global select_bucket
        bucket = int(select_bucket.get_active_id())

        if bucket > 0:
            cursor.execute("SELECT * FROM buckets WHERE id = ? ",(bucket,))
            row = cursor.fetchone()

            builder.get_object("host").set_text(row[2])
            builder.get_object("key").set_text(row[3])
            builder.get_object("secret").set_text(row[4])
            builder.get_object("bucket").set_text(row[1])

    def on_save_clicked(self, button):
        host = builder.get_object("host").get_text()
        key = builder.get_object("key").get_text()
        secret = builder.get_object("secret").get_text()
        bucket = builder.get_object("bucket").get_text()

        if host != "" and key != "" and secret != "" and bucket != "" :
            results = cursor.execute("SELECT COUNT(id), * FROM buckets WHERE bucket = ? ",(bucket,)).fetchone()
            count = results[0]
            #print(count)
            if count == 0:
                cursor.execute("INSERT INTO buckets (bucket, host, key, secret) VALUES (?, ? , ? ,?) ",(bucket, host, key, secret))
                status_msg = lang["msg_created"]
            else:
                bucket_id = results[1]
                cursor.execute("UPDATE buckets SET bucket = ?, host = ?, key = ?, secret = ? WHERE id = ?",(bucket, host, key, secret, bucket_id))
                status_msg = lang["msg_updated"]
            conn.commit()

            set_status(status_msg)
            print(status_msg)
            
            builder.get_object("host").set_text("")
            builder.get_object("key").set_text("")
            builder.get_object("secret").set_text("")
            builder.get_object("bucket").set_text("")

            create_select_bucket()
        else:
            set_status(lang['msg_fields'])

    def on_delete_clicked(self, button):
        global select_bucket
        bucket = int(select_bucket.get_active_id())
        if bucket > 0:
            dialog = builder.get_object('dialog1')
            response = dialog.run()
            dialog.hide()

    def on_btn_delete_ok_clicked(self, button):
        dialog = builder.get_object('dialog1')
        dialog.hide()

        global select_bucket
        bucket = int(select_bucket.get_active_id())
        if bucket > 0:
            cursor.execute("DELETE FROM buckets WHERE id = ? ",(bucket,))
            status_msg = lang["msg_deleted"]
        conn.commit()

        set_status(status_msg)
        print(status_msg)

        builder.get_object("host").set_text("")
        builder.get_object("key").set_text("")
        builder.get_object("secret").set_text("")
        builder.get_object("bucket").set_text("")

        create_select_bucket()

    def on_btn_delete_cancel_clicked(self, button):
        dialog = builder.get_object('dialog1')
        dialog.hide()


def create_select_bucket():
    global select_bucket
    select_bucket.remove_all()
    select_bucket.insert(0, "0", lang['select_bucket'])

    position = 1
    for row in cursor.execute("SELECT id, bucket FROM buckets ORDER BY bucket ASC"):
        select_bucket.insert(position, str(row[0]), row[1])
        position = position + 1

    select_bucket.set_active_id("0")

def set_labels():
    builder.get_object("window1").set_title(lang["title"])
    builder.get_object("key").modify_font(Pango.FontDescription('Sans 12'))
    builder.get_object("host").modify_font(Pango.FontDescription('Sans 12'))
    builder.get_object("bucket").modify_font(Pango.FontDescription('Sans 12'))
    builder.get_object("mount").set_label(lang["mount_bucket"])
    builder.get_object("unmount").set_label(lang["unmount_bucket"])
    builder.get_object("lbl_host").set_label(lang["hostname"]+":")
    builder.get_object("lbl_host").set_xalign(1)
    builder.get_object("lbl_key").set_label(lang["access_key"]+":")
    builder.get_object("lbl_key").set_xalign(1)
    builder.get_object("lbl_secret").set_label(lang["secret_key"]+":")
    builder.get_object("lbl_secret").set_xalign(1)
    builder.get_object("lbl_bucket").set_label(lang["bucket"]+":")
    builder.get_object("lbl_bucket").set_xalign(1)

    builder.get_object("dialog1").set_title(lang["delete"])
    builder.get_object("delete_lbl").set_label(lang["delete_dialog"])
    builder.get_object("btn_delete_cancel").set_label(lang["cancel"])

def get_language():
    lang = locale.getlocale()[0][0:2]
    filename = "lang/"+lang+".json"
    if os.path.exists(filename):
        lang_file = open(filename, "r")
    else:
        lang_file = open("lang/"+default_lang+".json", "r")

    return lang_file.read()

def set_status(msg):
    builder.get_object("status").set_text(msg)
    t = Timer(10, clear_status)
    t.start()

def clear_status():
    builder.get_object("status").set_text("")

if __name__ == '__main__':
    main()