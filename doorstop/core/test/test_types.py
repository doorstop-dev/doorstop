"""Unit tests for the doorstop.core.types module."""

import unittest

from doorstop.core.types import ID, Level


class TestID(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the ID class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.id = ID('REQ001')


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
        self.assertEqual((1,), Level(()).value)
        self.assertEqual((1, 0), Level(Level('1.0')).value)

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

    def test_lt(self):
        """Verify levels can be compared."""
        self.assertLess(self.level_1, self.level_1_2)
        self.assertLess(self.level_1_2, [1, 3])
        self.assertGreater(self.level_1_2_3, self.level_1_2)

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

    def test_lshift_empty(self):
        """Verify levels can be dedented."""
        level = self.level_1_2_3
        level <<= 4
        self.assertEqual(Level('1'), level)

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
