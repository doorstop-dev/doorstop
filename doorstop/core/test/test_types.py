"""Unit tests for the doorstop.core.types module."""

import unittest

from doorstop.common import DoorstopError
from doorstop.core.types import Prefix, ID, Text, Level


class TestPrefix(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the Prefix class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.prefix1 = Prefix('REQ')
        self.prefix2 = Prefix('TST (@/tst)')

    def test_init(self):
        """Verify prefixes are parsed correctly."""
        self.assertIs(self.prefix1, Prefix(self.prefix1))
        self.assertEqual(Prefix(''), Prefix())
        self.assertEqual(Prefix(''), Prefix(None))
        self.assertEqual(Prefix(''), Prefix(''))

    def test_init_reseved(self):
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


class TestID(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the ID class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.id1 = ID('REQ001')
        self.id2 = ID('TST-02')
        self.id3 = ID('SYS', '-', 3, 5)

    def test_init(self):
        """Verify IDs are parsed correctly."""
        self.assertIs(self.id1, ID(self.id1))
        identifier = ID('REQ')
        self.assertRaises(DoorstopError, getattr, identifier, 'prefix')
        identifier = ID('REQ-?')
        self.assertRaises(DoorstopError, getattr, identifier, 'number')
        self.assertRaises(TypeError, ID, 'REQ', '-')
        self.assertRaises(TypeError, ID, 'REQ', '-', 42)
        self.assertRaises(TypeError, ID, 'REQ', '-', 42, 3, 'extra')
        self.assertEqual(ID(''), ID())
        self.assertEqual(ID(''), ID(None))

    def test_repr(self):
        """Verify IDs can be represented."""
        self.assertEqual("ID('REQ001')", repr(self.id1))
        self.assertEqual("ID('TST-02')", repr(self.id2))
        self.assertEqual("ID('SYS-00003')", repr(self.id3))

    def test_str(self):
        """Verify IDs can be converted to strings."""
        self.assertEqual('REQ001', str(self.id1))
        self.assertEqual('TST-02', str(self.id2))
        self.assertEqual('SYS-00003', str(self.id3))

    def test_eq(self):
        """Verify IDs can be equated."""
        self.assertEqual(ID('REQ.001'), ID('req', '', 1, 3))
        self.assertEqual(ID('REQ1'), ID('REQ', '', 1, 3))
        self.assertNotEqual(ID('REQ.2'), ID('REQ', '-', 1, 3))
        self.assertEqual(ID('REQ1'), ID('REQ001 (@/req1.yml)'))
        self.assertEqual('req1', ID('REQ001'))
        self.assertNotEqual(None, ID('REQ001'))

    def test_sort(self):
        """Verify IDs can be sorted."""
        ids = [ID('a'), ID('a1'), ID('a2'), ID('b')]
        self.assertListEqual(ids, sorted(ids))

    def test_prefix(self):
        """Verify IDs have prefixes."""
        self.assertEqual('REQ', self.id1.prefix)
        self.assertEqual('TST', self.id2.prefix)
        self.assertEqual('SYS', self.id3.prefix)

    def test_number(self):
        """Verify IDs have numbers."""
        self.assertEqual(1, self.id1.number)
        self.assertEqual(2, self.id2.number)
        self.assertEqual(3, self.id3.number)


class TestText(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the Text class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.text = Text("Hello, \nworld! ")

    def test_init(self):
        """Verify Text is parsed correctly."""
        self.assertEqual(Text(""), Text())
        self.assertEqual(Text(""), Text(None))
        self.assertEqual(Text(""), Text(""))

    def test_repr(self):
        """Verify text can be represented."""
        self.assertEqual("'Hello, world!'", repr(self.text))

    def test_str(self):
        """Verify text can be converted to strings."""
        self.assertEqual("Hello, world!", str(self.text))

    def test_eq(self):
        """Verify text can be equated."""
        self.assertEqual(Text("Hello, world!"), self.text)

    def test_yaml(self):
        """Verify levels can be converted to their YAML representation."""
        self.assertEqual("Hello, world!\n", self.text.yaml)


class TestLevel(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the Level class."""  # pylint: disable=C0103,W0212

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
        self.assertEqual("Level('1.2', heading=True)",
                         repr(self.level_1_2_heading))
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


class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.types module."""  # pylint: disable=C0103

    pass
