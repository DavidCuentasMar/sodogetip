import time
import traceback

import praw
from praw.models import Message, Comment
from tinydb import TinyDB

import bot_command
import bot_logger
import commands
import config
import crypto
import lang
import utils
from models import UserStorage, VanityGenRequest


class SoDogeTip:
    def __init__(self):
        pass

    def main(self):
        bot_logger.logger.info('Main Bot loop !')

        while True:
            try:
                reddit = praw.Reddit(config.bot_name)

                for msg in reddit.inbox.unread(limit=None):

                    if (type(msg) is not Message) and (type(msg) is not Comment):
                        bot_logger.logger.info('Not a good message !')
                        msg.reply(lang.message_not_supported)
                        utils.mark_msg_read(reddit, msg)
                    else:
                        bot_logger.logger.info("%s - %s sub : %s" % (str(msg), msg.author.name, msg.subject))
                        msg_body = msg.body.strip()
                        msg_subject = msg.subject.strip()
                        split_message = msg_body.lower().split()

                        if msg_subject == '+register' or split_message.count('+register'):
                            commands.register_user(msg)
                            utils.mark_msg_read(reddit, msg)

                        elif msg_subject == '+info' or msg_subject == '+balance':
                            commands.info_user(msg)
                            utils.mark_msg_read(reddit, msg)

                        elif msg_subject == '+help':
                            commands.help_user(msg)
                            utils.mark_msg_read(reddit, msg)

                        elif msg_subject == '+history':
                            commands.history_user(msg)
                            utils.mark_msg_read(reddit, msg)

                        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
                            utils.mark_msg_read(reddit, msg)
                            commands.withdraw_user(msg)

                        elif split_message.count('+/u/' + config.bot_name):
                            utils.mark_msg_read(reddit, msg)
                            commands.tip_user(msg)

                        elif split_message.count('+donate'):
                            utils.mark_msg_read(reddit, msg)
                            commands.donate(msg)

                        elif split_message.count('+halloffame'):
                            utils.mark_msg_read(reddit, msg)
                            commands.hall_of_fame(msg)

                        elif split_message.count('+vanity'):
                            utils.mark_msg_read(reddit, msg)
                            commands.vanity(msg)

                        elif msg_subject == '+gold' or msg_subject == '+gild':
                            commands.gold(reddit, msg)
                            utils.mark_msg_read(reddit, msg)

                        else:
                            utils.mark_msg_read(reddit, msg)
                            # msg.reply('Currently not supported')
                            bot_logger.logger.info('Currently not supported')

                # to not explode rate limit :)
                #bot_logger.logger.info('Make an pause !')
                time.sleep(3)
            except:
                traceback.print_exc()
                bot_logger.logger.error('Main Bot loop crashed...')
                time.sleep(10)

    def process_pending_tip(self):
        while True:
            bot_logger.logger.info('Make clean of unregistered tips')
            bot_command.replay_pending_tip()
            time.sleep(3600)

    def anti_spamming_tx(self):
        # protect against spam attacks of an address having UTXOs.
        while True:
            rpc_antispam = crypto.get_rpc()

            bot_logger.logger.info('Make clean of tx')
            # get list of account
            list_account = UserStorage.get_users()
            if len(list_account) > 0:
                for account in list_account:
                    address = UserStorage.get_user_address(account)
                    if address is not None:
                        # don't flood rpc daemon
                        time.sleep(1)
                        list_tx = rpc_antispam.listunspent(1, 99999999999, [address])

                        if len(list_tx) > int(config.spam_limit):
                            unspent_amounts = []
                            for i in range(0, len(list_tx), 1):
                                unspent_amounts.append(list_tx[i]['amount'])
                                # limits to 200 transaction to not explode timeout rpc
                                if i > 200:
                                    break

                            bot_logger.logger.info('Consolidate %s account !' % account)
                            crypto.send_to(rpc_antispam, address, address, sum(unspent_amounts), True)

            # wait a bit before re-scan account
            time.sleep(240)

    def vanitygen(self):
        while True:
            bot_logger.logger.info('Check if we need to generate address')
            # get user request of gen
            db = TinyDB(config.vanitygen)
            for gen_request in db.all():
                vanity_request = VanityGenRequest.create_from_array(gen_request)

                # send message to warn user (it's start)
                vanity_request.user.send_private_message("Vanity Generation : Start",
                                                         "Vanity address generation have start :)")

                # generate address
                vanity_request.generate()

                # import address into wallet (set account of this address) - no rescan
                if vanity_request.import_address():
                    # make sure address is correctly import before move fund

                    time_start = time.time()
                    # transfer funds
                    vanity_request.move_funds()

                    # set request finish (add time)
                    time_end = time.time()
                    vanity_request.duration = (time_end - time_start)
                    vanity_request.update_data()

                    #  send message to warn user (it's finish)
                    vanity_request.user.send_private_message("Vanity Generation : Finish",
                                                             "Vanity address is finish, you can use our new address, and thanks to support %s" % config.bot_name)

            # wait a bit before re-check
            time.sleep(300)
