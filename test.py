import unittest

from main import *
from parser import build


class Tests(unittest.TestCase):

    def check_events(self, state: StationState, n: int, expected: List[TrainEvent]):
        state.step_n(n)
        events = state.current_events()
        self.assertEqual(expected, events)
        state.reset_events()

    def test_events(self):
        station, timetable = build("a.txt")
        state = StationState(station)
        state.add_timetable(timetable)

        self.check_events(state, 2, [TrainEvent(2, "1437", TrainState.BeingFormed, "4", "C")])
        self.check_events(state, 12, [TrainEvent(12, "1437", TrainState.Scheduled, "4", "C")])
        self.check_events(state, 20, [TrainEvent(20, "1437", TrainState.Railed, "4", "C"),
                                      TrainEvent(20, "7382", TrainState.Scheduled, "2", "B")])
        self.check_events(state, 23, [TrainEvent(23, "8493", TrainState.Scheduled, "1", "A")])
        # self.check_events(state, 7, [TrainEvent(30, "7382", TrainState.Railed, "2", "B")])


