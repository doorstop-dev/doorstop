"""Unit tests for the doorstop.core.types module."""

import unittest

from doorstop.core.types import Level


class TestLevel(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the Level class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.level_1 = Level('1')
        self.level_1_2 = Level('1.2')
        self.level_1_2_heading = Level('1.2.0')
        self.level_1_2_3 = Level('1.2.3')

    def test_str(self):
        """Verify levels can be converted to strings."""
        self.assertEqual('1', str(self.level_1))
        self.assertEqual('1.2', str(self.level_1_2))
        self.assertEqual('1.2.0', str(self.level_1_2_heading))
        self.assertEqual('1.2.3', str(self.level_1_2_3))

    def test_eq(self):
        """Verify levels can be equated."""
        self.assertNotEqual(self.level_1, self.level_1_2)
        self.assertEqual(self.level_1_2, Level([1, 2]))
        self.assertEqual(self.level_1_2, (1, 2))
        self.assertEqual(self.level_1_2, self.level_1_2_heading)

    def test_lt(self):
        """Verify levels can be compared."""
        self.assertLess(self.level_1, self.level_1_2)
        self.assertLess(self.level_1_2, [1, 3])
        self.assertGreater(self.level_1_2_3, self.level_1_2)

    def test_iadd(self):
        """Verify levels can be incremented."""
        level = self.level_1_2
        level += 1
        self.assertEqual(Level('1.3'), level)

    def test_iadd_heading(self):
        """Verify (heading) levels can be incremented."""
        level = self.level_1_2_heading
        level += 2
        self.assertEqual(Level('1.4.0'), level)

    def test_isub(self):
        """Verify levels can be decremented."""
        level = self.level_1_2_3
        level -= 2
        self.assertEqual(Level('1.2.1'), level)

    def test_isub_heading(self):
        """Verify (heading) levels can be decremented."""
        level = self.level_1_2_heading
        level -= 1
        self.assertEqual(Level('1.1.0'), level)

    def test_isub_zero(self):
        """Verify levels cannot be decremented to zero."""
        level = self.level_1_2
        level -= 2
        self.assertEqual(Level('1.1'), level)

    def test_irshift(self):
        """Verify levels can be indented."""
        level = self.level_1_2
        level >>= 1
        self.assertEqual(Level('1.2.1'), level)

    def test_irshift_heading(self):
        """Verify (heading) levels can be indented."""
        level = self.level_1_2_heading
        level >>= 2
        self.assertEqual(Level('1.2.1.1.0'), level)

    def test_ilshift(self):
        """Verify levels can be dedented."""
        level = self.level_1_2_3
        level <<= 2
        self.assertEqual(Level('1'), level)

    def test_ilshift_heading(self):
        """Verify (heading) levels can be dedented."""
        level = self.level_1_2_heading
        level <<= 1
        self.assertEqual(Level('1.0'), level)

    def test_ilshift_empty(self):
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


class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.types module."""  # pylint: disable=C0103

    pass
