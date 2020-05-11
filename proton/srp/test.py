import unittest

from .testdata import instances
from .testserver import TestServer
from .util import *
from ._ctsrp import User as CTUser
from ._pysrp import User as PYUser


class SRPTestCases:
    class SRPTestBase(unittest.TestCase):
        def test_invalid_version(self):
            modulus = bytes.fromhex(instances[0]['Modulus'])
            salt = base64.b64decode(instances[0]['Salt'])

            with self.assertRaises(ValueError):
                usr = self.user('user', 'pass', modulus)
                usr.compute_v(salt, 2)

            with self.assertRaises(ValueError):
                usr = self.user('user', 'pass', modulus)
                usr.compute_v(salt, 5)

        def test_generate_v(self):
            for instance in instances:

                if instance["Exception"] is not None:
                    with self.assertRaises(instance['Exception']):
                        usr = self.user(instance["Username"], instance["Password"], bytes.fromhex(instance["Modulus"]))
                        usr.compute_v(base64.b64decode(instance["Salt"]), PM_VERSION)
                else:
                    usr = self.user(instance["Username"], instance["Password"], bytes.fromhex(instance["Modulus"]))
                    v = usr.compute_v(base64.b64decode(instance["Salt"]), PM_VERSION)

                    self.assertFalse(
                        instance['Exception'],
                        "Expected exception while generating v, instance: " + str(instance)[:30] + "..."
                    )
                    self.assertEqual(
                        instance["Verifier"],
                        base64.b64encode(v).decode('utf8'),
                        "Wrong output while generating v, instance: " + str(instance)[:30] + "..."
                    )

        def test_srp(self):
            for instance in instances:
                if instance["Exception"]:
                    continue

                server = TestServer(
                    instance["Username"],
                    bytes.fromhex(instance["Modulus"]),
                    base64.b64decode(instance["Verifier"])
                )

                server_challenge = server.get_challenge()
                usr = self.user(instance["Username"], instance["Password"], bytes.fromhex(instance["Modulus"]))

                _, client_challenge = usr.start_authentication()
                client_proof = usr.process_challenge(base64.b64decode(instance["Salt"]), server_challenge, PM_VERSION)
                server_proof = server.process_challenge(client_challenge, client_proof)
                usr.verify_session(server_proof)

                self.assertIsNotNone(
                    client_proof,
                    "SRP exchange failed, client_proof is none for instance: " + str(instance)[:30] + "..."
                )

                self.assertFalse(
                    instance['Exception'],
                    "Expected exception while performing auth, instance: " + str(instance)[:30] + "..."
                )

                self.assertEqual(
                    server.get_session_key(),
                    usr.get_session_key(),
                    "Secrets do not match, instance: " + str(instance)[:30] + "..."
                )

                self.assertTrue(
                    server.get_authenticated(),
                    "Server is not correctly authenticated, instance:: " + str(instance)[:30] + "..."
                )

                self.assertTrue(
                    usr.authenticated(),
                    "User is not correctly authenticated, instance:: " + str(instance)[:30] + "..."
                )


class TestCTSRPClass(SRPTestCases.SRPTestBase):
    def setUp(self):
        self.user = CTUser


class TestPYSRPClass(SRPTestCases.SRPTestBase):
    def setUp(self):
        self.user = PYUser


if __name__ == '__main__':
    unittest.main()
