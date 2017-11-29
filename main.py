import os
import time
import traceback
from threading import Thread

import bot_logger
import config
import crypto
import dogetipper

if __name__ == "__main__":
    bot_logger.logger.info("Bot Started !!")

    for coin in config.rpc_config.keys():
        # get wallet pass phrase from user input
        crypto.init_passphrase(coin)

        # check passphase is good for all coin
        crypto.check_passphrase(coin)

    while True:
        try:
            # create directory to store user history
            if not os.path.exists(config.history_path):
                os.makedirs(config.history_path)

            # thread to process reddit commands
            thread_master = Thread(name='app', target=dogetipper.main)

            # thread to process pending tips
            thread_pending_tip = Thread(name='pending_tip', target=dogetipper.process_pending_tip)

            # some security thread
            thread_anti_spamming_tx = Thread(name='anti_spam', target=dogetipper.anti_spamming_tx)

            if config.vanity_enabled:
                thread_vanity = Thread(name='vanitygen', target=dogetipper.vanitygen)
                thread_vanity.setDaemon(True)
                thread_vanity.start()

            thread_master.start()
            thread_pending_tip.start()
            thread_anti_spamming_tx.start()

            thread_master.join()
            thread_pending_tip.join()
            thread_anti_spamming_tx.join()

            bot_logger.logger.error('All bot task finished ...')
        except:
            traceback.print_exc()
            bot_logger.logger.error('Resuming in 30sec...')
            time.sleep(30)
