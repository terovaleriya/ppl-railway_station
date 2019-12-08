import unittest

from src.main import *
from src.parser import build


class Tests(unittest.TestCase):

    #     def test_rails(self):
    #         station = Station()
    #         station.add_rail(Rail("1"))
    #         station.add_rail("2")
    #         station.add_rail("3")
    #         station.add_rail("4")
    #         station.add_platform("A", 5)
    #         station.add_platform("B", 6)
    #         station.add_platform("C", 3)
    #         station.add_link("1", "A")
    #         station.add_link("2", "A")
    #         station.add_link("3", "B")
    #         station.add_link("4", "B")
    #
    #         self.assertEqual(station.rails.count, 4)
    #         self.assertEqual(station.platforms.count, 3)
    #         self.assertEqual(station.prl.count, 2)

    def test_buld(self):
        build("a.txt")

#
# if __name__ == '__main__':
#     unittest.main()
