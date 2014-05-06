
import doorstop
import unittest

from profilehooks import profile

class test_profile(unittest.TestCase):

    def test_profile_issues(self):
        print ("profiling issues")
        tree = doorstop.build()
        print (profile(tree.issues))

if __name__ == '__main__':
    unittest.main()