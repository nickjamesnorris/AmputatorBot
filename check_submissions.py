# This Python file uses the following encoding: utf-8
# License: GPL-3 (https://choosealicense.com/licenses/gpl-3.0/)
# Original author: Killed_Mufasa
# Twitter: https://twitter.com/Killed_Mufasa
# Reddit:  https://www.reddit.com/user/Killed_Mufasa
# GitHub:  https://github.com/KilledMufasa
# Website: https://www.amputatorbot.com
# Donate:  https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=EU6ZFKTVT9VH2

# This wonderful little program is used by u/AmputatorBot
# (https://www.reddit.com/user/AmputatorBot) to scan submissions
# in certain subreddits for AMP links. If AmputatorBot detects an
# AMP link, a reply is made with the direct link

# Import a couple of libraries
import logging
import traceback
from time import sleep

import util

logging.basicConfig(
    filename="logs/v1.9/check_submissions.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

# Main function. Gets the stream for submissions in certain subreddits,
# scans the context for AMP links and replies with the direct link
def run_bot(r, allowed_subreddits, forbidden_users, np_subreddits, submissions_replied_to, submissions_unable_to_reply):
    logging.info("Praw: obtaining stream of subreddits")

    # Get the submission stream of select subreddits using Praw.
    for submission in r.subreddit("+".join(allowed_subreddits)).stream.submissions():
        # Resets for every submission
        canonical_urls = []
        reply = ""
        reply_generated = ""
        success = False
        item = submission
        domain = "www"
        note = "\n\n"
        note_alt = "\n\n"

        try:
            # Set body in accordance to the instance
            item_body = util.get_body(item)

            # If the item contains an AMP link and meets the other criteria, fetch the canonical link(s)
            if check_criteria(item, item_body):
                try:
                    logging.debug("#{}'s body: {}\nScanning for urls..".format(item.id, item_body))
                    try:
                        amp_urls = util.get_amp_urls(item_body)
                        if not amp_urls:
                            logging.info("Couldn't find any amp urls")
                        else:
                            for x in range(len(amp_urls)):
                                if util.check_if_google(amp_urls[x]):
                                    note = " This page is even fully hosted by Google (!).\n\n"
                                    note_alt = " Some of these pages are even fully hosted by Google (!).\n\n"
                                    break
                            canonical_urls, warning_log = util.get_canonicals(amp_urls, True)
                            latest_warning = str(warning_log[-1])
                            if canonical_urls:
                                reply_generated = '\n\n'.join(canonical_urls)

                            else:
                                logging.info("No canonical urls were found, error log:\n" + latest_warning)
                    except:
                        logging.warning("Couldn't check amp_urls")

                # If the program fails to find any link at all, throw an exception
                except:
                    logging.error(traceback.format_exc())
                    logging.warning("No links were found.\n")

                # If no canonical urls were found, don't reply
                if len(canonical_urls) == 0:
                    fatal_error_message = "there were no canonical URLs found"
                    logging.warning("[STOPPED] " + fatal_error_message + "\n\n")

                # If there were direct links found, reply!
                else:
                    # Try to reply to OP
                    try:
                        canonical_urls_amount = len(canonical_urls)

                        # If the subreddit encourages the use of NP, make it NP
                        if item.subreddit in np_subreddits:
                            domain = "np"

                        # If there was only one url found, generate a simple comment
                        if canonical_urls_amount == 1:
                            reply = "It looks like OP posted an AMP link. These will often load faster, but Google's AMP [threatens the Open Web](https://www.socpub.com/articles/chris-graham-why-google-amp-threat-open-web-15847) and [your privacy](https://" + domain + ".reddit.com/r/AmputatorBot/comments/ehrq3z/why_did_i_build_amputatorbot)." + note + "You might want to visit **the normal page** instead: **[" + canonical_urls[0] + "](" + canonical_urls[0] + ")**.\n\n*****\n\n​^(I'm a bot | )[^(Why & About)](https://" + domain + ".reddit.com/r/AmputatorBot/comments/ehrq3z/why_did_i_build_amputatorbot)^( | )[^(Mention me to summon me!)](https://" + domain + ".reddit.com/r/AmputatorBot/comments/cchly3/you_can_now_summon_amputatorbot/)"

                        # If there were multiple urls found, generate a multi-url comment
                        if canonical_urls_amount > 1:
                            # Generate entire comment
                            reply = "It looks like OP shared a couple of AMP links. These will often load faster, but Google's AMP [threatens the Open Web](https://www.socpub.com/articles/chris-graham-why-google-amp-threat-open-web-15847) and [your privacy](https://" + domain + ".reddit.com/r/AmputatorBot/comments/ehrq3z/why_did_i_build_amputatorbot)." + note_alt + "You might want to visit **the normal pages** instead: \n\n" + reply_generated + "\n\n*****\n\n​^(I'm a bot | )[^(Why & About)](https://" + domain + ".reddit.com/r/AmputatorBot/comments/ehrq3z/why_did_i_build_amputatorbot)^( | )[^(Mention me to summon me!)](https://" + domain + ".reddit.com/r/AmputatorBot/comments/cchly3/you_can_now_summon_amputatorbot/)"

                        # Reply to item
                        item.reply(reply)
                        logging.debug("Replied to #{}\n".format(item.id))

                        # If the reply was successfully send, note this
                        success = True
                        with open("submissions_replied_to.txt", "a") as f:
                            f.write(item.id + ",")
                        submissions_replied_to.append(item.id)
                        logging.info("Added the item id to file: submissions_replied_to.txt\n\n\n")

                    # If the reply didn't got through, throw an exception
                    # This can occur when item gets deleted or when rate limits are exceeded
                    except:
                        logging.error(traceback.format_exc())
                        fatal_error_message = "could not reply to item, it either got deleted or the rate-limits have been exceeded"
                        logging.warning("[STOPPED] " + fatal_error_message + "\n\n")

                # If the reply could not be made or send, note this
                if not success:
                    with open("submissions_unable_to_reply.txt", "a") as f:
                        f.write(item.id + ",")
                    submissions_unable_to_reply.append(item.id)
                    logging.info("Added the item id to file: submissions_unable_to_reply.txt.")

        except:
            logging.error(traceback.format_exc())
            fatal_error_message = "could not find amp body or check criteria"
            logging.warning("[STOPPED] " + fatal_error_message + "\n\n")


def check_criteria(item, item_body):
    # Must contain an AMP link
    if not util.check_if_amp(item_body):
        return False
    # Must not be an item that previously failed
    if item.id in submissions_unable_to_reply:
        return False
    # Must not be already replied to
    if item.id in submissions_replied_to:
        return False
    # Must not be posted by me
    if item.author == r.user.me():
        return False
    # Must not be posted by a user who opted out
    if str(item.author) in forbidden_users:
        return False

    # If all criteria were met, return True
    return True


# Uses these functions to run the bot
r = util.bot_login()
forbidden_users = util.get_forbidden_users()
allowed_subreddits = util.get_allowed_subreddits()
np_subreddits = util.get_np_subreddits()
submissions_replied_to = util.get_submissions_replied()
submissions_unable_to_reply = util.get_submissions_errors()


# Run the program
while True:
    try:
        run_bot(r, allowed_subreddits, forbidden_users, np_subreddits, submissions_replied_to,
                submissions_unable_to_reply)
    except:
        logging.warning("Couldn't log in or find the necessary files! Waiting 120 seconds")
        sleep(120)