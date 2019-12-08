import datetime
from abc import ABC
from typing import List, Dict, Tuple, Any, Union, Callable
from enum import Enum

DT = int


class Rail:
    def __init__(self, id: str):
        self.id = id


class Platform:
    max_cars: int

    def __init__(self, id: str, max_cars: int):
        self.max_cars = max_cars
        self.id = id


class PlatformRailLink:
    def __init__(self, platform: Platform, rail: Rail):
        self.platform = platform
        self.rail = rail


class Station:
    rails: Dict[str, Rail]
    platforms: Dict[str, Platform]
    links: List[PlatformRailLink]

    def __init__(self):
        self.rails = dict()
        self.platforms = dict()
        self.prl = []

    def add_rail(self, rail: Rail):
        self.rails[rail.id] = rail

    def add_platform(self, platform: Platform):
        self.platforms[platform.id] = platform

    def add_link(self, rail_id: str, platform_id: str):
        rail = self.rails[rail_id]
        platform = self.platforms[platform_id]
        linked = PlatformRailLink(platform, rail)
        self.prl.append(linked)

    def get_rail(self, id: str) -> Rail:
        rail = self.rails[id]
        return rail

    def get_platform(self, id: str) -> Platform:
        platform = self.platforms[id]
        return platform

    def get_rails_for_platform(self, id: str) -> List[Rail]:
        pass

    def get_platform_for_rail(self, id: str) -> List[Platform]:
        pass


class Direction(Enum):
    Forward = True
    Back = False


class Action(Enum):
    Form = 1
    Disband = -1
    Pass = 0


class TimetableEntry:
    arrival: DT
    departure: DT
    cars: int
    direction: Direction
    action: Action

    def __init__(self, arrival: DT, departure: DT, cars: int):
        self.arrival = arrival
        self.departure = departure
        self.cars = cars


class Timetable:
    entries: List[TimetableEntry]

    def __init__(self, entries: List[TimetableEntry]):
        self.entries = entries


class TrainState:
    entry: TimetableEntry
    rail: Rail
    platform: Platform
    delay: int  # минуты


class RailState:
    id: str


class PlatformState:
    id: str


class CarType(Enum):
    Locomotive = 1
    Passenger = 2


class TechTrain:
    id: str


class TrainState(Enum):
    Unscheduled = 0
    Scheduled = 1
    Railed = 2
    DelayedArrival = 3
    DelayedDeparture = 4
    Departed = 5
    Disbanded = 6
    BeingFormed = 7
    Cancelled = 8

    # unscheduled=>scheduled=>railed=>departed
    # unscheduled=>scheduled=>railed=>disbanded
    # unscheduled=>being formed=>railed=>departed
    # unscheduled=>being formed=>railed=>disbanded
    def terminal(self):
        return self == TrainState.Departed or self == TrainState.Disbanded or self == TrainState.Cancelled


class TimetableEntryState:
    entry: TimetableEntry
    state: TrainState = TrainState.Unscheduled
    rail: Rail
    platform: Platform
    delay: int = 0

    def __init__(self, entry: TimetableEntry):
        self.entry = entry

    def schedule(self, rail: Rail, platform: Platform):
        self.rail = rail
        self.platform = platform


class StationState:
    transition_processors: Dict[Tuple[TrainState, TrainState], Callable[[TimetableEntryState], None]]
    state_processors: Dict[TrainState, Callable[[TimetableEntryState], None]]
    ts: DT = 0
    station: Station
    timetable: Timetable
    entries: List[TimetableEntryState]

    def __init__(self, station: Station):
        self.station = station
        self.state_processors = {
            TrainState.Unschedule: self.process_unscheduled,
            TrainState.Scheduled: self.process_scheduled,
            TrainState.DelayedArrival: self.process_delayed_arrival,
            TrainState.Railed: self.process_railed,
        }
        self.transition_processors = {
            (None, TrainState.Scheduled): self.transit_to_scheduled,
            (TrainState.Unschedule, None): self.transit_from_unscheduled,
            (None, TrainState.Disbanded): self.leave_station,
            (None, TrainState.Departed): self.leave_station,
        }

    def add_timetable(self, timetable: Timetable):
        for entry in timetable.entries:
            self.entries.append(TimetableEntryState(entry))

    def step(self):
        self.ts = self.ts + 1
        for entry in filter(lambda t: not t.state.terminal(), self.entries):
            self.state_processors[entry.state](entry)

    def available(self, rail: Rail, platform: Platform) -> bool:
        return True

    def change_state(self, entry: TimetableEntryState, new_state: TrainState):
        old_state = entry.state
        entry.state = new_state
        for key, fn in self.transition_processors.items():
            f, t = key
            if (not f or f == old_state) and (not t or t == new_state):
                fn(entry)

    def transit_to_scheduled(self, entry: TimetableEntryState):
        pass

    def transit_from_unscheduled(self, entry: TimetableEntryState):
        pass

    def leave_station(self, entry: TimetableEntryState):
        pass

    def process_unscheduled(self, entry: TimetableEntryState):
        if TrainState.entry.action == 1:
            if entry.entry.arrival - self.ts <= 30:
                self.change_state(entry, TrainState.BeingFormed)
        elif entry.entry.arrival - self.ts <= 10:
            self.change_state(entry, TrainState.Scheduled)
            # available = self.find_available(entry)
            # if not available:
            #     entry.state = TrainState.DelayedArrival
            # else
            #     entry.schedule()pass
            pass

    def process_scheduled(self, entry: TimetableEntryState):
        if entry.entry.arrival == self.ts:
            if self.available(entry.rail, entry.platform):
                self.change_state(entry, TrainState.Railed)
            else:
                self.change_state(entry, TrainState.DelayedArrival)
        entry.delay = self.ts - entry.entry.arrival

    def process_delayed_arrival(self, entry: TimetableEntryState):
        if self.available(entry.rail, entry.platform):
            self.change_state(entry, TrainState.Railed)
        else:
            self.change_state(entry, TrainState.DelayedArrival)
        entry.delay = self.ts - entry.entry.departure

    def process_railed(self, entry: TimetableEntryState):
        if self.ts >= entry.entry.departure:
            entry.state = TrainState.DelayedDeparture
        elif self.ts >= entry.entry.departure + entry.delay:
            if TimetableEntryState.entry.action == Action.Disband:
                self.change_state(entry, TrainState.Disbanded)
            else:
                self.change_state(entry, TrainState.Departed)

    def process_being_formed(self, entry: TimetableEntryState):
        if entry.entry.arrival - self.ts <= 20:
            if self.available(entry.rail, entry.platform):
                self.change_state(entry, TrainState.Railed)
        else:
            self.change_state(entry, TrainState.DelayedArrival)
        entry.delay = self.ts - entry.entry.arrival

    def process_delayed_departure(self, entry: TimetableEntryState):
        if self.ts >= entry.entry.departure:
            self.change_state(entry, TrainState.DelayedDeparture)

    def process_disbanded(self, entry: TimetableEntryState):
        if self.ts >= entry.entry.departure:
            self.change_state(entry, TrainState.DelayedDeparture)
        elif self.ts >= entry.entry.departure + entry.delay:
            self.change_state(entry, TrainState.Disbanded)
