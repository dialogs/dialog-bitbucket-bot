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


def handle_relevant_comment(data, pull_author_username):
    # There's a bug on the render side than doesn't render markdown correctly
    # if more than one link is on the same line
    # Dirty Fix here: |^| \n
    text = "[{username}]({user_link})\n" \
           "{action} on [{repo_name}]({repo_link})\n" \
           "{text_content}\n" \
           "[View Comment]({comment_link})\n" \
           "{msg_date}".format(**data)
    # Send Message
    user_peer = None
    try:
        user_peer = bot.users.find_user_outpeer_by_nick(pull_author_username)
    except:
        log.error("User_id of {0} not found".format(pull_author_username))
    if user_peer:
        bot.messaging.send_message(user_peer, text)


def analyze_comments(data, server_api=False):
    max_time = None
    for current in data:
        if "comment" in current:  # Yes there are comments on this pull
            try:
                # Retrieve some useful data from API response
                if server_api:
                    evt = {"comment_id": current["comment"]["id"],
                           "username": current["comment"]["author"]["displayName"],
                           "user_link": current["comment"]["author"]["links"]["self"][0]["href"],
                           "text_content": current["comment"]["text"],
                           "create_date": datetime.datetime.fromtimestamp(current["comment"]["createdDate"] / 1000,
                                                                          tz=datetime.timezone.utc),
                           "update_date": datetime.datetime.fromtimestamp(current["comment"]["updatedDate"] / 1000,
                                                                          tz=datetime.timezone.utc)}
                else:
                    evt = {"username": current["comment"]["user"]["display_name"],
                           "user_link": current["comment"]["user"]["links"]["html"]["href"],
                           "pull_title": current["comment"]["pullrequest"]["title"],
                           "pull_link": current["comment"]["pullrequest"]["links"]["html"]["href"],
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
                yield evt
            except:
                log.error("Exception", exc_info=True)
                continue
    # if new comments has been elaborated move forward the time indicator
    if max_time:
        PERSISTENT_STORAGE["last_time"] = max_time


def reminder_loop():
    while True:
        users_waiting = []

        # Checking local data is faster than an API request
        for user_uid, user_opts in PERSISTENT_STORAGE["users"].items():
            try:
                if user_opts["notify_time"]:  # Time is set
                    now = datetime.datetime.now(datetime.timezone.utc)
                    preferred_time = user_opts["notify_time"]
                    # Check time
                    if now.minute == preferred_time.minute and now.hour == preferred_time.hour and now.second == 0:
                        users_waiting.append(user_uid)
            except:
                log.error("Exception", exc_info=True)
                continue
        # if at least 1 user is expecting a reminder right now, perform API requests
        if users_waiting:
            try:
                # Generate Reminder text
                text = ""
                pending = []
                server_api = current_settings["bitbucket"]["server_api"]
                if server_api:
                    repo_gen = API.get_repositories(current_settings["bitbucket"]["project"]["name"])
                else:
                    repo_gen = API.get_repositories(current_settings["bitbucket"]["repository"]["user"])

                for current_repo in repo_gen:
                    # Analyze_open_pulls
                    if server_api:
                        pull_gen = API.get_pulls(current_repo["project"]["key"], current_repo["slug"])
                    else:
                        pull_gen = API.get_pulls(current_repo["owner"]["username"], current_repo["name"])
                    for current_pull in pull_gen:
                        if current_pull["state"] == "OPEN":
                            if server_api:
                                pull_link = current_pull["links"]["self"][0]["href"]
                            else:
                                pull_link = current_pull["links"]["html"]["href"]
                            pending.append((current_pull["title"], pull_link))

                    if len(pending) > 0:
                        if text == "":
                            text += "Daily reminder\n"
                        text += "Pending pull requests for {0}\n".format(current_repo["name"])
                        for p_title, p_url in pending:
                            text += ">[{0}]({1})\n".format(p_title, p_url)
                # Send reminder to users
                if text != "":
                    for user_uid in users_waiting:
                        try:
                            user_peer = bot.users.get_user_outpeer_by_id(int(user_uid))
                            if user_peer:
                                bot.messaging.send_message(user_peer, text)
                        except:
                            log.error("Exception", exc_info=True)
                            continue
            except:
                log.error("Exception", exc_info=True)
                continue
        time.sleep(0.8)


def activity_monitor_loop_server():
    while True:
        try:
            for current_repo in API.get_repositories(current_settings["bitbucket"]["project"]["name"]):
                for current_pull in API.get_pulls(current_repo["project"]["key"], current_repo["slug"]):
                    try:
                        pull_author_username = current_pull["author"]["user"]["name"]
                        # API CALL Limited to 1 Page (for recent events)
                        activity = API.get_pulls_activity(current_repo["project"]["key"], current_repo["slug"],
                                                          current_pull["id"], max_pages=1)
                        for event in analyze_comments(activity, True):
                            if current_settings["ignore_comment_updates"] and event["update"]:
                                # Ignore edit comments
                                continue
                            msg_date = (event["create_date"] if event["update"] else event["update_date"])
                            tmp = event
                            tmp["action"] = "Edited his comment" if event["update"] else "commented"
                            tmp["repo_name"] = current_repo["name"]
                            tmp["repo_link"] = current_repo["links"]["self"][0]["href"]
                            tmp["msg_date"] = msg_date.strftime("%Y-%m-%d - %H:%M:%S %Z")
                            tmp["pull_title"] = current_pull["title"]
                            tmp["pull_link"] = current_pull["links"]["self"][0]["href"]
                            tmp["comment_link"] = API.format_comment_url(current_repo["project"]["key"],
                                                                         current_repo["slug"],
                                                                         current_pull["id"], event["comment_id"])

                            handle_relevant_comment(tmp, pull_author_username)

                        time.sleep(current_settings["sleep_time_secs"])
                    except:
                        log.error("Exception", exc_info=True)
                        continue
        except:
            log.error("Exception", exc_info=True)
            continue


def activity_monitor_loop_cloud():
    while True:
        try:
            for current_repo in API.get_repositories(current_settings["bitbucket"]["repository"]["user"]):
                for current_pull in API.get_pulls(current_repo["owner"]["username"], current_repo["name"]):
                    try:
                        pull_author_username = current_pull["author"]["username"]
                        # API CALL Limited to 1 Page (for recent events)
                        activity = API.get_pull_activity(current_repo["owner"]["username"],
                                                         current_repo["name"],
                                                         current_pull["id"], 1)
                        for event in analyze_comments(activity):
                            if current_settings["ignore_comment_updates"] and event["update"]:
                                # Ignore edit comments
                                continue
                            msg_date = event["create_date"] if event["update"] else event["update_date"]
                            tmp = event
                            tmp["action"] = "Edited his comment" if event["update"] else "commented"
                            tmp["repo_name"] = current_repo["name"]
                            tmp["repo_link"] = current_repo["links"]["self"]["href"]
                            tmp["msg_date"] = msg_date.strftime("%Y-%m-%d - %H:%M:%S %Z")
                            handle_relevant_comment(tmp, pull_author_username)

                        time.sleep(current_settings["sleep_time_secs"])
                    except:
                        log.error("Exception", exc_info=True)
                        continue
        except:
            log.error("Exception", exc_info=True)
            continue


def on_msg(*params):
    for param in params:
        log.debug("onMsg -> {}".format(param))
        if param.peer.id == param.sender_uid:
            try:
                txt = param.message.textMessage.text
                if txt.startswith("/disableReminder"):
                    log.debug("disableReminder")
                    if str(param.sender_uid) in PERSISTENT_STORAGE["users"]:
                        del PERSISTENT_STORAGE["users"][str(param.sender_uid)]
                        PERSISTENT_STORAGE.dump()  # operations on child objects requires manual dump
                    bot.messaging.send_message(param.peer, "Success. I will not send you the reminder anymore.")

                elif txt.startswith("/setReminder"):
                    log.debug("setTime")
                    stext = txt[txt.find(" ") + 1:]
                    reminder_time = datetime.datetime.strptime(stext, "%H:%M %z")
                    PERSISTENT_STORAGE["users"][str(param.sender_uid)] = {
                        "notify_time": reminder_time.astimezone(datetime.timezone.utc)
                    }
                    PERSISTENT_STORAGE.dump()  # operations on child objects requires manual dump
                    bot.messaging.send_message(param.peer,
                                               "Success, ok I will send you a reminder every day at {0}".format(
                                                   reminder_time.strftime("%H:%M:%S %z")))

                elif txt.startswith("/help"):
                    bot.messaging.send_message(param.peer, HELP_TEXT)

                else:
                    bot.messaging.send_message(param.peer, "Command not found.")
                    bot.messaging.send_message(param.peer, HELP_TEXT)

            except:
                bot.messaging.send_message(param.peer, "Failed. see /help")
                log.error("Exception", exc_info=True)
                continue


if __name__ == '__main__':
    SETTINGS_PATH = os.path.dirname(__file__) + "/../settings.json"
    STORAGE_PATH = os.path.dirname(__file__) + "/../storage.json"

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
        if "users" not in PERSISTENT_STORAGE or not PERSISTENT_STORAGE["users"]:
            PERSISTENT_STORAGE["users"] = {}
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
            if current_settings["bitbucket"]["server_api"]:
                from BitBucketServeruAPI import BitBucketServeruAPI as BitBucketuAPI
            else:
                from BitBucketClouduAPI import BitBucketClouduAPI as BitBucketuAPI
            API = BitBucketuAPI(current_settings["bitbucket"]["endpoint"],
                                auth=(os.environ.get('USERNAME'),
                                      os.environ.get('PASSWORD')))
        except:
            log.error("API init", exc_info=True)
            sys.exit(1)

        try:
            bot = DialogBot.get_secure_bot(
                os.environ.get('BOT_ENDPOINT'),  # bot endpoint
                grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
                os.environ.get('BOT_TOKEN')  # bot token
            )
            if current_settings["bitbucket"]["server_api"]:
                threading.Thread(target=activity_monitor_loop_server).start()
            else:
                threading.Thread(target=activity_monitor_loop_cloud).start()

            threading.Thread(target=reminder_loop).start()
            bot.messaging.on_message(on_msg)  # Blocking
        except:
            log.error("Can't initialize bot", exc_info=True)
            sys.exit(1)

    else:
        log.error("{0} not found."
                  "Create one using settings_default.json as reference.".format(SETTINGS_PATH), exc_info=True)
        sys.exit(1)
