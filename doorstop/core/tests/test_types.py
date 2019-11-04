# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.types module."""

import unittest

import yaml

from doorstop.common import DoorstopError
from doorstop.core.types import UID, Level, Prefix, Stamp, Text


class TestPrefix(unittest.TestCase):
    """Unit tests for the Prefix class."""  # pylint: disable=W0212

    def setUp(self):
        self.prefix1 = Prefix('REQ')
        self.prefix2 = Prefix('TST (@/tst)')

    def test_init_empty(self):
        """Verify prefixes are parsed correctly (empty)."""
        self.assertEqual(Prefix(''), Prefix())
        self.assertEqual(Prefix(''), Prefix(None))

    def test_init_instance(self):
        """Verify prefixes are parsed correctly (instance)."""
        self.assertIs(self.prefix1, Prefix(self.prefix1))
        self.assertEqual(Prefix(''), Prefix(None))
        self.assertEqual(Prefix(''), Prefix(''))

    def test_init_reserved(self):
        """Verify an exception is raised for a reserved word."""
        self.assertRaises(DoorstopError, Prefix, 'ALL')

    def test_repr(self):
        """Verify prefixes can be represented."""
        self.assertEqual("Prefix('REQ')", repr(self.prefix1))
        self.assertEqual("Prefix('TST')", repr(self.prefix2))

    def test_str(self):
        """Verify prefixes can be converted to strings."""
        self.assertEqual('REQ', str(self.prefix1))
        self.assertEqual('TST', str(self.prefix2))

    def test_eq(self):
        """Verify prefixes can be equated."""
        self.assertEqual(Prefix('REQ'), self.prefix1)
        self.assertNotEqual(self.prefix1, self.prefix2)
        self.assertEqual(Prefix('req'), self.prefix1)
        self.assertEqual('Req', self.prefix1)
        self.assertNotEqual(None, self.prefix1)
        self.assertNotEqual('all', self.prefix1)

    def test_sort(self):
        """Verify prefixes can be sorted."""
        prefixes = [Prefix('a'), Prefix('B'), Prefix('c')]
        self.assertListEqual(prefixes, sorted(prefixes))


class TestUID(unittest.TestCase):
    """Unit tests for the UID class."""  # pylint: disable=W0212

    def setUp(self):
        self.uid1 = UID('REQ001')
        self.uid2 = UID('TST-02')
        self.uid3 = UID('SYS', '-', 3, 5)
        self.uid4 = UID('REQ001', stamp='abc123')

    def test_init_str(self):
        """Verify UIDs are parsed correctly (string)."""
        uid = UID('REQ')
        self.assertRaises(DoorstopError, getattr, uid, 'prefix')
        self.assertRaises(DoorstopError, getattr, uid, 'number')
        self.assertRaises(DoorstopError, getattr, uid, 'name')
        uid = UID('REQ-?')
        self.assertRaises(DoorstopError, getattr, uid, 'prefix')
        self.assertRaises(DoorstopError, getattr, uid, 'number')
        self.assertRaises(DoorstopError, getattr, uid, 'name')

    def test_init_dict(self):
        """Verify UIDs are parsed correctly (dictionary)."""
        uid = UID({'REQ001': 'abc123'})
        self.assertEqual('REQ', uid.prefix)
        self.assertEqual(1, uid.number)
        self.assertEqual('', uid.name)
        self.assertEqual('abc123', uid.stamp)

    def test_init_name(self):
        """Verify UIDs are parsed correctly (name)."""
        uid = UID('REQ', '-', 'NAME')
        self.assertEqual('REQ', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('NAME', uid.name)
        uid = UID('REQ-NAME')
        self.assertEqual('REQ', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('NAME', uid.name)
        uid = UID('REQ-MIDDLE-NAME')
        self.assertEqual('REQ-MIDDLE', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('NAME', uid.name)
        uid = UID('REQ.A-B_C')
        self.assertEqual('REQ.A-B', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('C', uid.name)
        uid = UID('REQ.A-B_C more')
        self.assertEqual('REQ.A-B', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('C', uid.name)
        uid = UID('REQ.A-B_1C more')
        self.assertEqual('REQ.A-B', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('1C', uid.name)
        uid = UID('REQ.A-B_C2 more')
        self.assertEqual('REQ.A-B', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('C2', uid.name)
        uid = UID('REQ.A-B_C3D more')
        self.assertEqual('REQ.A-B', uid.prefix)
        self.assertEqual(-1, uid.number)
        self.assertEqual('C3D', uid.name)

    def test_init_values(self):
        """Verify UIDs are parsed correctly (values)."""
        self.assertRaises(TypeError, UID, 'REQ', '-')
        self.assertRaises(TypeError, UID, 'REQ', '-', 42, 3, 'extra')

    def test_init_empty(self):
        """Verify UIDs are parsed correctly (empty)."""
        self.assertEqual(UID(''), UID())
        self.assertEqual(UID(''), UID(None))

    def test_init_instance(self):
        """Verify UIDs are parsed correctly (instance)."""
        self.assertIs(self.uid1, UID(self.uid1))
        self.assertIs(self.uid4, UID(self.uid4))

    def test_repr(self):
        """Verify UIDs can be represented."""
        self.assertEqual("UID('REQ001')", repr(self.uid1))
        self.assertEqual("UID('TST-02')", repr(self.uid2))
        self.assertEqual("UID('SYS-00003')", repr(self.uid3))
        self.assertEqual("UID('REQ001', stamp='abc123')", repr(self.uid4))

    def test_str(self):
        """Verify UIDs can be converted to strings."""
        self.assertEqual('REQ001', str(self.uid1))
        self.assertEqual('TST-02', str(self.uid2))
        self.assertEqual('SYS-00003', str(self.uid3))

    def test_eq(self):
        """Verify UIDs can be equated."""
        self.assertEqual(UID('REQ.001'), UID('req', '', 1, 3))
        self.assertEqual(UID('REQ1'), UID('REQ', '', 1, 3))
        self.assertNotEqual(UID('REQ.2'), UID('REQ', '-', 1, 3))
        self.assertEqual(UID('REQ1'), UID('REQ001 (@/req1.yml)'))
        self.assertEqual('req1', UID('REQ001'))
        self.assertNotEqual(None, UID('REQ001'))
        self.assertEqual(self.uid1, self.uid4)
        self.assertEqual(UID('a', '-', 'b'), UID('a', '-', 'b'))
        self.assertNotEqual(UID('a', '-', 'b'), UID('a', '-', 'c'))

    def test_le(self):
        """Verify UID's less operator."""
        self.assertTrue(UID('a', '-', 1, 0) < UID('a', '-', 2, 0))
        self.assertFalse(UID('a', '-', 1, 0) < UID('a', '-', 1, 0))
        self.assertFalse(UID('a', '-', 2, 0) < UID('a', '-', 1, 0))
        self.assertTrue(UID('a', '-', 'a') < UID('a', '-', 'b'))
        self.assertFalse(UID('a', '-', 'a') < UID('a', '-', 'a'))
        self.assertFalse(UID('a', '-', 'b') < UID('a', '-', 'a'))
        self.assertTrue(UID('a', '-', 'a') < UID('a', '-', 1, 0))
        self.assertFalse(UID('a', '-', 1, 0) < UID('a', '-', 'a'))

    def test_sort(self):
        """Verify UIDs can be sorted."""
        uids = [UID('a'), UID('a1'), UID('a2'), UID('b')]
        self.assertListEqual(uids, sorted(uids))

    def test_prefix(self):
        """Verify UIDs have prefixes."""
        self.assertEqual('REQ', self.uid1.prefix)
        self.assertEqual('TST', self.uid2.prefix)
        self.assertEqual('SYS', self.uid3.prefix)

    def test_number(self):
        """Verify UIDs have numbers."""
        self.assertEqual(1, self.uid1.number)
        self.assertEqual(2, self.uid2.number)
        self.assertEqual(3, self.uid3.number)

    def test_string(self):
        """Verify UIDs can be converted to string including stamps."""
        self.assertEqual("REQ001", self.uid1.string)
        self.assertEqual("REQ001:abc123", self.uid4.string)

    def test_stamp(self):
        """Verify stamps are stored correctly."""
        self.assertEqual('abc123', self.uid4.stamp)
        self.assertEqual('abc123', UID(self.uid4).stamp)
        self.assertEqual('def456', UID(self.uid4, stamp='def456').stamp)
        self.assertEqual(True, UID({'REQ001': 1}).stamp)
        self.assertEqual(True, UID("REQ001:1").stamp)


class TestText(unittest.TestCase):
    """Unit tests for the Text class."""  # pylint: disable=W0212

    def setUp(self):
        self.text = Text("Hello, \nworld! ")

    def test_init(self):
        """Verify Text is parsed correctly."""
        self.assertEqual(Text(""), Text())
        self.assertEqual(Text(""), Text(None))
        self.assertEqual(Text(""), Text(""))

    def test_repr(self):
        """Verify text can be represented."""
        self.assertEqual("'Hello,\\nworld!'", repr(self.text))

    def test_str(self):
        """Verify text can be converted to strings."""
        self.assertEqual("Hello,\nworld!", str(self.text))

    def test_eq(self):
        """Verify text can be equated."""
        self.assertEqual(Text("Hello,\nworld!"), self.text)

    def test_yaml(self):
        """Verify levels can be converted to their YAML representation."""
        self.assertEqual('Hello,\nworld!\n', self.text.yaml)

    def test_dump_yaml(self):
        """Verify levels can be converted to their YAML representation."""
        text = Text('Hello,\n World!\n')
        self.assertEqual('|\n  Hello,\n   World!\n', yaml.dump(text.yaml))

    def test_dump_yaml_space(self):
        """Text starting with a space is encoded to a yaml literal string."""
        text = Text(' abc ')
        self.assertEqual('|2\n   abc\n', yaml.dump(text.yaml))

    def test_dump_yaml_space_before_newline(self):
        """Text starting with a space is encoded to a yaml literal string."""
        text = Text('hello \nworld\n')
        self.assertEqual('|\n  hello\n  world\n', yaml.dump(text.yaml))


class TestLevel(unittest.TestCase):
    """Unit tests for the Level class."""  # pylint: disable=W0212

    def setUp(self):
        self.level_1 = Level('1')
        self.level_1_2 = Level('1.2')
        self.level_1_2_heading = Level('1.2.0')
        self.level_1_2_3 = Level('1.2.3')

    def test_init(self):
        """Verify levels can be parsed."""
        self.assertEqual((1, 0), Level((1, 0)).value)
        self.assertEqual((1,), Level((1)).value)
        self.assertEqual((1, 0), Level(Level('1.0')).value)
        self.assertEqual((1, 0), Level(1, heading=True).value)
        self.assertEqual((1,), Level((1, 0), heading=False).value)
        self.assertEqual((1,), Level())
        self.assertEqual((1,), Level(None))
        self.assertEqual((1,), Level(()).value)
        self.assertEqual((1,), Level(0).value)
        self.assertEqual((1,), Level('').value)
        self.assertEqual((0,), Level((0,)).value)
        self.assertEqual((0,), Level('0').value)
        self.assertEqual((0,), Level('0.0').value)

    def test_repr(self):
        """Verify levels can be represented."""
        self.assertEqual("Level('1')", repr(self.level_1))
        self.assertEqual("Level('1.2')", repr(self.level_1_2))
        self.assertEqual("Level('1.2', heading=True)", repr(self.level_1_2_heading))
        self.assertEqual("Level('1.2.3')", repr(self.level_1_2_3))

    def test_str(self):
        """Verify levels can be converted to strings."""
        self.assertEqual('1', str(self.level_1))
        self.assertEqual('1.2', str(self.level_1_2))
        self.assertEqual('1.2.0', str(self.level_1_2_heading))
        self.assertEqual('1.2.3', str(self.level_1_2_3))

    def test_len(self):
        """Verify a level length is equal to number of non-heading parts."""
        self.assertEqual(1, len(self.level_1))
        self.assertEqual(2, len(self.level_1_2))
        self.assertEqual(2, len(self.level_1_2_heading))
        self.assertEqual(3, len(self.level_1_2_3))

    def test_eq(self):
        """Verify levels can be equated."""
        self.assertNotEqual(self.level_1, self.level_1_2)
        self.assertEqual(self.level_1_2, Level([1, 2]))
        self.assertEqual(self.level_1_2, (1, 2))
        self.assertEqual(self.level_1_2, self.level_1_2_heading)

    def test_eq_other(self):
        """Verify levels can be equated with non-levels."""
        self.assertNotEqual(self.level_1, None)
        self.assertEqual((1, 2, 0), self.level_1_2_heading)
        self.assertEqual((1, 2), self.level_1_2_heading)

    def test_compare(self):
        """Verify levels can be compared."""
        self.assertLess(self.level_1, self.level_1_2)
        self.assertLessEqual(self.level_1, self.level_1)
        self.assertLessEqual(self.level_1, self.level_1_2)
        self.assertLess(self.level_1_2, [1, 3])
        self.assertGreater(self.level_1_2_3, self.level_1_2)
        self.assertGreaterEqual(self.level_1_2_3, self.level_1_2)
        self.assertGreaterEqual(self.level_1_2_3, self.level_1_2_3)

    def test_hash(self):
        """Verify level's can be hashed."""
        levels = {Level('1.2'): 1, Level('1.2.3'): 2}
        self.assertIn(self.level_1_2, levels)
        self.assertNotIn(self.level_1_2_heading, levels)

    def test_add(self):
        """Verify levels can be incremented."""
        level = self.level_1_2
        level += 1
        self.assertEqual(Level('1.3'), level)
        self.assertEqual(Level('1.5'), level + 2)

    def test_add_heading(self):
        """Verify (heading) levels can be incremented."""
        level = self.level_1_2_heading
        level += 2
        self.assertEqual(Level('1.4.0'), level)

    def test_sub(self):
        """Verify levels can be decremented."""
        level = self.level_1_2_3
        level -= 1
        self.assertEqual(Level('1.2.2'), level)
        self.assertEqual(Level('1.2.1'), level - 1)

    def test_sub_heading(self):
        """Verify (heading) levels can be decremented."""
        level = self.level_1_2_heading
        level -= 1
        self.assertEqual(Level('1.1.0'), level)

    def test_sub_zero(self):
        """Verify levels cannot be decremented to zero."""
        level = self.level_1_2
        level -= 2
        self.assertEqual(Level('1.1'), level)

    def test_rshift(self):
        """Verify levels can be indented."""
        level = self.level_1_2
        level >>= 1
        self.assertEqual(Level('1.2.1'), level)
        self.assertEqual(Level('1.2.1.1'), level >> 1)

    def test_rshift_heading(self):
        """Verify (heading) levels can be indented."""
        level = self.level_1_2_heading
        level >>= 2
        self.assertEqual(Level('1.2.1.1.0'), level)

    def test_rshift_negative(self):
        """Verify levels can be indented negatively."""
        level = self.level_1_2_3
        level >>= -1
        self.assertEqual(Level('1.2'), level)
        self.assertEqual(Level('1'), level >> -1)

    def test_lshift(self):
        """Verify levels can be dedented."""
        level = self.level_1_2_3
        level <<= 1
        self.assertEqual(Level('1.2'), level)
        self.assertEqual(Level('1'), level << 1)

    def test_lshift_heading(self):
        """Verify (heading) levels can be dedented."""
        level = self.level_1_2_heading
        level <<= 1
        self.assertEqual(Level('1.0'), level)

    def test_lshift_negative(self):
        """Verify levels can be dedented negatively."""
        level = self.level_1_2_3
        level <<= -1
        self.assertEqual(Level('1.2.3.1'), level)
        self.assertEqual(Level('1.2.3.1.1'), level << -1)

    def test_lshift_empty(self):
        """Verify levels can be dedented."""
        level = self.level_1_2_3
        level <<= 4
        self.assertEqual(Level('1'), level)

    def test_lshift_zero(self):
        """Verify detenting levels by zero has no effect.."""
        level = self.level_1_2_3
        level <<= 0
        self.assertEqual(Level('1.2.3'), level)

    def test_value(self):
        """Verify levels can be converted to their values."""
        self.assertEqual((1,), self.level_1.value)
        self.assertEqual((1, 2), self.level_1_2.value)
        self.assertEqual((1, 2, 0), self.level_1_2_heading.value)
        self.assertEqual((1, 2, 3), self.level_1_2_3.value)

    def test_yaml(self):
        """Verify levels can be converted to their YAML representation."""
        self.assertEqual(1, self.level_1.yaml)
        self.assertEqual(1.2, self.level_1_2.yaml)
        self.assertEqual('1.2.0', self.level_1_2_heading.yaml)
        self.assertEqual('1.2.3', self.level_1_2_3.yaml)

    def test_copy(self):
        """Verify levels can be copied."""
        level = self.level_1_2.copy()
        self.assertEqual(level, self.level_1_2)
        level += 1
        self.assertNotEqual(level, self.level_1_2)


class TestStamp(unittest.TestCase):
    """Unit tests for the Stamp class."""  # pylint: disable=W0212

    def setUp(self):
        self.stamp1 = Stamp('abc123')
        self.stamp2 = Stamp("Hello, world!", 42, False)
        self.stamp3 = Stamp(True)
        self.stamp4 = Stamp(False)
        self.stamp5 = Stamp()

    def test_repr(self):
        """Verify stamps can be represented."""
        self.assertEqual("Stamp('abc123')", repr(self.stamp1))
        self.assertEqual(
            "Stamp('u0t4qETWyPPPzcRu5K_2iCMAGgfLN8bDP4enBHqBsWg=')", repr(self.stamp2)
        )
        self.assertEqual("Stamp(True)", repr(self.stamp3))
        self.assertEqual("Stamp(None)", repr(self.stamp4))
        self.assertEqual("Stamp(None)", repr(self.stamp5))

    def test_str(self):
        """Verify stamps can be converted to strings."""
        self.assertEqual('abc123', str(self.stamp1))
        self.assertEqual(
            'u0t4qETWyPPPzcRu5K_2iCMAGgfLN8bDP4enBHqBsWg=', str(self.stamp2)
        )
        self.assertEqual('', str(self.stamp3))
        self.assertEqual('', str(self.stamp4))
        self.assertEqual('', str(self.stamp5))

    def test_bool(self):
        """Verify stamps can be converted to boolean."""
        self.assertTrue(self.stamp1)
        self.assertTrue(self.stamp2)
        self.assertTrue(self.stamp3)
        self.assertFalse(self.stamp4)
        self.assertFalse(self.stamp5)

    def test_eq(self):
        """Verify stamps can be equated."""
        self.assertEqual('abc123', self.stamp1)
        self.assertEqual('u0t4qETWyPPPzcRu5K_2iCMAGgfLN8bDP4enBHqBsWg=', self.stamp2)
        self.assertEqual(True, self.stamp3)
        self.assertEqual(None, self.stamp4)
        self.assertNotEqual(self.stamp1, self.stamp2)
        self.assertNotEqual(self.stamp3, self.stamp4)
        self.assertEqual(self.stamp4, self.stamp5)

    def test_yaml(self):
        """Verify stamps can be converted to their YAML dump format."""
        self.assertEqual('abc123', self.stamp1.yaml)
        self.assertEqual(
            'u0t4qETWyPPPzcRu5K_2iCMAGgfLN8bDP4enBHqBsWg=', self.stamp2.yaml
        )
        self.assertEqual(True, self.stamp3.yaml)
        self.assertEqual(None, self.stamp4.yaml)
        self.assertEqual(None, self.stamp5.yaml)
