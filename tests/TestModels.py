import copy
import datetime
import unittest

import config
import models
import user_function
from tests.MockRpc import MockRpc


class TestTip(unittest.TestCase):
    def test_tip_simple(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 100 " + config.coin_name, None)
        self.assertEqual(100, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_simpl_float_comma(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 10,8 " + config.coin_name, None)
        self.assertEqual(10, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_simple_float_dot(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 10.8 " + config.coin_name, None)
        self.assertEqual(10, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_simple_float_dot_long(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 0.000000001 doge", None)
        self.assertEqual(0.000000001, float(tip.amount))
        self.assertEqual("doge", tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_simple_verify(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 100 " + config.coin_name + " verify", None)
        self.assertEqual(100, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(True, tip.verify)

    def test_tip_random(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " random100 " + config.coin_name + "", None)
        self.assertLess(tip.amount, 100)
        self.assertGreater(tip.amount, 1)
        self.assertEqual("doge", tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_roll(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " roll " + config.coin_name + " verify", None)
        self.assertLessEqual(tip.amount, 6)
        self.assertGreaterEqual(tip.amount, 1)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(True, tip.verify)

    def test_tip_flip(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " flip " + config.coin_name + " verify", None)
        self.assertLessEqual(tip.amount, 2)
        self.assertGreaterEqual(tip.amount, 1)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(True, tip.verify)

    def test_tip_dogecar(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " dogecar " + config.coin_name + " verify", None)
        self.assertEqual(tip.amount, config.tip_keyword['dogecar'])
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual(True, tip.verify)

    def test_tip_random_verify(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " random10000 " + config.coin_name, None)
        self.assertLess(tip.amount, 10000)
        self.assertGreater(tip.amount, 1)
        self.assertEqual(config.coin_name, tip.currency)
        if tip.amount >= 1000:
            self.assertEqual(True, tip.verify)

    def test_tip_user_mention(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " /u/just-an-dev 1000 " + config.coin_name, None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_user_mention_add(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " +/u/just-an-dev 1000 " + config.coin_name, None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_user_mention_at(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " @just-an-dev 1000 " + config.coin_name, None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_negative(self):
        tip = models.Tip()
        self.assertRaises(AttributeError, tip.parse_message,
                          "+/u/" + config.bot_name + " -99999999 " + config.coin_name + " verify", None)

    def test_tip_address(self):
        mock_rpc = MockRpc()
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR 1000 " + config.coin_name,
                          mock_rpc)
        tip.set_sender('just-an-dev')
        self.assertEqual(1000, tip.amount)
        self.assertEqual(config.coin_name, tip.currency)
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", tip.receiver.address)
        self.assertEqual("address-nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", tip.receiver.username)

    def test_tip_not_expired(self):
        tip = models.Tip()
        tip.time = datetime.datetime.now()
        self.assertEqual(False, tip.is_expired())

    def test_tip_expired(self):
        tip = models.Tip()
        tip.time = datetime.datetime.now() - datetime.timedelta(days=5)
        self.assertEqual(True, tip.is_expired())

    def test_tip_unregistered(self):
        list_tips = user_function.get_unregistered_tip()

        tip = models.Tip().create_from_array(list_tips[2])
        self.assertEqual(True, tip.is_expired())

    def test_create_from_array(self):
        list_tips = user_function.get_unregistered_tip()

        # make a copy for tests :)
        list_tips_edit = copy.deepcopy(list_tips)

        tip = models.Tip().create_from_array(list_tips_edit[1])
        self.assertEqual(list_tips[1]['amount'], tip.amount)
        self.assertEqual(list_tips[1]['sender'], tip.sender.username)
        self.assertEqual(list_tips[1]['receiver'], tip.receiver.username)
        self.assertEqual(list_tips[1]['message_fullname'], tip.message_fullname)
        self.assertEqual(list_tips[1]['time'], tip.time)
        self.assertEqual(list_tips[1]['id'], tip.id)


class TestUser(unittest.TestCase):
    def test_user_is_registered(self):
        user = models.User("just-an-dev")
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", user.address)
        self.assertEqual(True, user.is_registered())

    def test_user_exist(self):
        u1 = models.User('just-an-dev')
        u2 = models.User('Just-An-dEv')
        u3 = models.User('not-exist')
        self.assertEqual(True, u1.is_registered())
        self.assertEqual(True, u2.is_registered())
        self.assertEqual(False, u3.is_registered())

        self.assertEqual(True, models.UserStorage.exist('just-an-dev'))
        self.assertEqual(True, models.UserStorage.exist('Just-An-dEv'))

    def test_user_not_exist(self):
        user = models.User("doge")
        self.assertEqual(None, user.address)
        self.assertEqual(False, user.is_registered())

    def test_user_exist_by_addr(self):
        user = models.User("doge")
        user.address = "nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR"
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", user.address)
        self.assertEqual(True, user.is_registered())

    def test_unregistered_tip_empty(self):
        user = models.User("doge")
        self.assertEqual(0, user.get_balance_pending_tip())

    def test_unregistered_tip(self):
        user = models.User("just-an-dev")
        self.assertEqual(1000, user.get_balance_pending_tip())

    def test_new_config(self):
        self.assertEqual('test_config', models.User(config.bot_name).address)

    def test_register(self):
        user = models.User("just-an-dev")
        mock_rpc = MockRpc()
        user.get_new_address(mock_rpc)
        user.register()


class TestUserStorage(unittest.TestCase):
    def test_get_user_new(self):
        self.assertIn('sodogetiptest', models.UserStorage.get_users())
        self.assertIn('just-an-dev', models.UserStorage.get_users())

    def test_get_user_addr(self):
        list = models.UserStorage.get_all_users_address()

        self.assertIn('test_config', list['sodogetiptest'])
        self.assertIn('nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR', list['just-an-dev'])

        self.assertIn('test_config', list.values())
        self.assertIn('nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR', list.values())

    def test_active_user_address(self):
        models.UserStorage.add_address("just-aN-New", "testing_addresss")
        models.UserStorage.active_user_address("jUst-an-new", "testing_addresss")
        user = models.User("Just-an-new")
        self.assertEqual(user.address, models.UserStorage.get_user_address("jusT-an-new"))
        self.assertEqual(True, user.is_registered())


if __name__ == '__main__':
    unittest.main()
