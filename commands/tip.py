from jinja2 import Template

import bot_logger
import crypto
import lang
import models
import user_function
import utils


def tip_user(msg):
    bot_logger.logger.info('An user mention detected ')

    # create an Tip
    tip = models.Tip()

    # update sender
    tip.set_sender(msg.author.name)

    # check user who use command is registered
    if tip.sender.is_registered() is not True:
        bot_logger.logger.info('user %s not registered (sender) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
        return False

    # parse message
    tip.parse_message(msg.body)

    # set reddit message id
    tip.message_fullname = msg.fullname

    # check amount of tip
    if not utils.check_amount_valid(tip.amount):
        # invalid amount
        bot_logger.logger.info(lang.message_invalid_amount)
        tip.sender.send_private_message('invalid amount', lang.message_invalid_amount)
        return False

    if tip.currency is None:
        bot_logger.logger.info(lang.message_invalid_currency)
        tip.sender.send_private_message('invalid currency', lang.message_invalid_currency)
        return False

    # update receiver
    tip.set_receiver(msg.parent().author.name)

    # check user not tip self
    if tip.sender.username == tip.receiver.username:
        tip.sender.send_private_message('cannot tip self',
                                        Template(lang.message_recipient_self).render(
                                            username=tip.sender.username))
        return False

    # check sender have enough
    user_balance = tip.sender.get_balance()
    bot_logger.logger.debug('user_balance = %s' % user_balance)

    # check user not send more they have (confirmed balance)
    if tip.amount > float(user_balance):

        user_pending_balance = user_balance + tip.sender.get_balance_unconfirmed()

        # not enough for tip (with unconfirmed balance)
        if tip.amount > float(user_pending_balance):
            bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                tip.sender.username, str(tip.amount), str(user_balance)))
            tip.sender.send_private_message('low balance',
                                            Template(lang.message_balance_low_tip).render(
                                                username=tip.sender.username))
            return False

        else:
            # we have to wait unconfirmed balance before process tip, add to queue
            pass
            # todo : add this to pendding tips
    else:

        # add tip to history of sender & receiver
        models.HistoryStorage.add_to_history_tip(tip.sender.username, "tip send", tip)
        models.HistoryStorage.add_to_history_tip(tip.receiver.username, "tip receive", tip)

        # check user who receive tip have an account
        if tip.receiver.is_registered():
            tip.tx_id = crypto.tip_user(tip.sender.address, tip.receiver.address, tip.amount)
            if tip.tx_id:
                tip.finish = True
                tip.status = 'ok'

                bot_logger.logger.info(
                    '%s tip %s to %s' % (msg.author.name, str(tip.amount), tip.receiver.username))

                # if user have 'verify' in this command he will have confirmation
                if tip.verify:
                    msg.reply(Template(lang.message_tip).render(
                        sender=tip.sender.username, receiver=tip.receiver.username,
                        amount=str(float(tip.amount)),
                        value_usd=str(tip.get_value_usd()), txid=tip.tx_id
                    ))
        else:
            bot_logger.logger.info('user %s not registered (receiver)' % tip.receiver.username)
            tip.status = "waiting registration of receiver"

            # save tip
            user_function.save_unregistered_tip(tip)

            # send message to sender of tip
            tip.sender.send_private_message('tipped user not registered',
                                            Template(lang.message_recipient_register).render(
                                                username=tip.receiver.username))
            # send message to receiver
            tip.receiver.send_private_message(
                Template(
                    lang.message_recipient_need_register_title).render(amount=str(tip.amount)),
                Template(
                    lang.message_recipient_need_register_message).render(
                    username=tip.receiver.username, sender=msg.author.name, amount=str(tip.amount),
                    value_usd=str(tip.get_value_usd())))

        # update tip status
        models.HistoryStorage.update_tip(tip.sender.username, tip)
        models.HistoryStorage.update_tip(tip.receiver.username, tip)
