# Python Standard Library
import sys
import os
import threading
import time
import datetime
import json
import logging

# Dialogs Python Bot SDK
import grpc
from dialog_bot_sdk.bot import DialogBot

from DictPersistJSON import DictPersistJSON
from BitBucketuAPI import BitBucketuAPI


def analyze_open_pulls(data):
    pending = []
    if "values" in data:
        for current in data["values"]:
            if current["state"] == "OPEN":
                pending.append((current["title"], current["links"]["html"]["href"]))
    return pending


def analyze_comments(data):
    events = []
    max_time = None
    if "values" in data:
        for current in data["values"]:
            if "comment" in current:  # Yes there are comments on this pull
                try:
                    # Retrieve some useful data from API response
                    evt = {"pull_title": current["comment"]["pullrequest"]["title"],
                           "pull_link": current["comment"]["pullrequest"]["links"]["html"]["href"],
                           "comment_user_name": current["comment"]["user"]["display_name"],
                           "comment_user_link": current["comment"]["user"]["links"]["html"]["href"],
                           "text_content": current["comment"]["content"]["raw"],
                           "comment_link": current["comment"]["links"]["html"]["href"],
                           "create_date": datetime.datetime.fromisoformat(current["comment"]["created_on"]),
                           "update_date": datetime.datetime.fromisoformat(current["comment"]["updated_on"])}

                    # if comment is posted after a predefined time it's a NEW comment
                    if evt["create_date"] > PERSISTENT_STORAGE["last_time"]:
                        evt["update"] = False
                        log.info("New Comment.")

                    # if comment is edited after a predefined time it's an UPDATED (aka EDITED) comment
                    elif evt["update_date"] > PERSISTENT_STORAGE["last_time"]:
                        evt["update"] = True
                        log.info("Updated Comment.")
                    else:
                        # ignore this comment it's old
                        continue
                    # move forward the time indicator to the latest message elaborated
                    if max_time is None or evt["create_date"] > max_time:
                        max_time = evt["create_date"]
                    if max_time is None or evt["update_date"] > max_time:
                        max_time = evt["update_date"]
                    events.append(evt)
                except:
                    log.error("Exception", exc_info=True)
                    continue
        # if new comments has been elaborated move forward the time indicator
        if max_time:
            PERSISTENT_STORAGE["last_time"] = max_time
    return events


def notify_loop():
    user_id = bot.users.get_user_outpeer_by_id(current_settings["user_id"])
    while 1:
        try:
            if PERSISTENT_STORAGE["notify_time"]:  # Time is set
                now = datetime.datetime.now(datetime.timezone.utc)
                if now.minute == PERSISTENT_STORAGE["notify_time"].minute and now.hour == PERSISTENT_STORAGE[
                    "notify_time"].hour and now.second == 0:  # Check time

                    user_repos = API.get_repositories(current_settings["bitbucket"]["repository"]["user"])
                    if "values" in user_repos:
                        text = ""
                        for current_repo in user_repos["values"]:
                            # Send report to user
                            api_res = API.get_pulls(current_settings["bitbucket"]["repository"]["user"],
                                                    current_repo["name"])
                            pending = analyze_open_pulls(api_res)
                            if len(pending) > 0:
                                if text == "":
                                    text += "Daily reminder\n"
                                text += "Pending pull requests for {0}/{1}\n".format(
                                    current_settings["bitbucket"]["repository"]["user"],
                                    current_repo["name"])
                                for p_title, p_url in pending:
                                    text += ">[{0}]({1})\n".format(p_title, p_url)
                        if text != "":
                            bot.messaging.send_message(user_id, text)
        except:
            log.error("Exception", exc_info=True)
            continue
        time.sleep(0.8)


def monitor_loop():
    user_id = bot.users.get_user_outpeer_by_id(current_settings["user_id"])
    while 1:
        user_repos = API.get_repositories(current_settings["bitbucket"]["repository"]["user"])
        if "values" in user_repos:
            for current_repo in user_repos["values"]:
                try:
                    act = API.get_pulls_activity(current_settings["bitbucket"]["repository"]["user"],
                                                 current_repo["name"])
                    for event in analyze_comments(act):
                        if current_settings["ignore_comment_updates"] and event["update"]:
                            # Ignore edit comments
                            continue
                        kind = "Edited his comment" if event["update"] else "commented"
                        msg_date = event["create_date"] if event["update"] else event["update_date"]
                        # There's a bug on the render side than doesn't render markdown correctly
                        # if more than one link is on the same line
                        # Dirty Fix here: |^| \n
                        text = "[{0}]({1})\n" \
                               "{2} on [{3}/{4}]({6})\n" \
                               "{7}\n" \
                               "[View Comment]({8})\n" \
                               "{9}".format(event["comment_user_name"], event["comment_user_link"],
                                            kind,
                                            current_settings["bitbucket"]["repository"]["user"],
                                            current_repo["name"],
                                            event["pull_title"],
                                            event["pull_link"],
                                            event["text_content"],
                                            event["comment_link"],
                                            msg_date.strftime("%Y-%m-%d - %H:%M:%S %Z"))
                        bot.messaging.send_message(user_id, text)

                    time.sleep(current_settings["sleep_time_secs"])
                except:
                    log.error("Exception", exc_info=True)
                    continue


def on_msg(*params):
    for param in params:
        log.debug("onMsg -> {}".format(param))
        if param.peer.id == param.sender_uid and param.sender_uid == current_settings["user_id"]:
            txt = param.message.textMessage.text

            if txt.startswith("/disableReminder"):
                log.debug("disableReminder")
                PERSISTENT_STORAGE["notify_time"] = None
                bot.messaging.send_message(param.peer, "Success. I will not send you the reminder anymore.")

            elif txt.startswith("/setReminder"):
                log.debug("setTime")
                try:
                    stext = txt[txt.find(" ") + 1:]
                    reminder_time = datetime.datetime.strptime(stext, "%H:%M %z")
                    PERSISTENT_STORAGE["notify_time"] = reminder_time.astimezone(datetime.timezone.utc)
                    bot.messaging.send_message(param.peer,
                                               "Success, ok I will send you a reminder every day at {0}".format(
                                                   reminder_time.strftime("%H:%M:%S %z")))
                except:
                    bot.messaging.send_message(param.peer, "Failed. see /help")
                    log.error("Exception", exc_info=True)
                    continue
            else:
                bot.messaging.send_message(param.peer, HELP_TEXT)


if __name__ == '__main__':
    SETTINGS_PATH = "../settings.json"
    STORAGE_PATH = "../storage.json"

    log = logging.getLogger("BitBucketBot")
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())
    log.info("Init")

    HELP_TEXT = "Welcome to Dialogs Bitbucket Bot\n" \
                "This bot can monitor your bitbucket's pull requests and notify you about new comments in real time," \
                "and send you a daily reminder for open pull requests\n" \
                "to enable the daily reminder you must specify a time using command:\n" \
                "/setReminder HH:MM OFFSET_TIMEZONE\n" \
                "Example (24h):\n" \
                "/setReminder 22:15 +0100\n" \
                "/setReminder 08:15 -0200\n" \
                "to disable notifications use\n" \
                "/disableReminder"

    try:
        PERSISTENT_STORAGE = DictPersistJSON(STORAGE_PATH)
        if "last_time" not in PERSISTENT_STORAGE or not PERSISTENT_STORAGE["last_time"]:
            # Handle only new messages
            PERSISTENT_STORAGE["last_time"] = datetime.datetime.now(datetime.timezone.utc)
        if "notify_time" not in PERSISTENT_STORAGE:
            # Notifications Disabled
            PERSISTENT_STORAGE["notify_time"] = None
    except:
        log.error("Can't load persistent storage", exc_info=True)
        sys.exit(1)

    if os.path.exists(SETTINGS_PATH):
        try:
            current_settings = json.load(open(SETTINGS_PATH))
        except:
            log.error("Can't load settings", exc_info=True)
            sys.exit(1)

        try:
            API = BitBucketuAPI(current_settings["bitbucket"]["endpoint"],
                                auth=(current_settings["bitbucket"]["auth"]["username"],
                                      current_settings["bitbucket"]["auth"]["password"]))
        except:
            log.error("API init", exc_info=True)
            sys.exit(1)

        try:
            bot = DialogBot.get_secure_bot(
                os.environ.get('BOT_ENDPOINT'),  # bot endpoint
                grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
                os.environ.get('BOT_TOKEN')  # bot token
            )
            threading.Thread(target=monitor_loop).start()
            threading.Thread(target=notify_loop).start()
            bot.messaging.on_message(on_msg)  # Blocking
        except:
            log.error("Can't initialize bot", exc_info=True)
            sys.exit(1)

    else:
        log.error("{0} not found."
                  "Create one using settings_default.json as reference.".format(SETTINGS_PATH), exc_info=True)
        sys.exit(1)
