from abc import ABC
from enum import Enum
from typing import List, Dict, Tuple, Callable, NamedTuple

from typeses import DT, TrainId, RailId, PlatformId


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
        self.links = []

    def add_rail(self, rail: Rail):
        self.rails[rail.id] = rail

    def add_platform(self, platform: Platform):
        self.platforms[platform.id] = platform

    def add_link(self, rail_id: str, platform_id: str):
        rail = self.rails[rail_id]
        platform = self.platforms[platform_id]
        linked = PlatformRailLink(platform, rail)
        self.links.append(linked)

    def get_rail(self, id: str) -> Rail:
        rail = self.rails[id]
        return rail

    def get_platform(self, id: str) -> Platform:
        platform = self.platforms[id]
        return platform

    def get_rails_for_platform(self, id: str) -> List[Rail]:
        f = filter(lambda t: t.platform.id == id, self.links)
        return list(map(lambda t: self.rails[t.rail.id], f))

    def get_platform_for_rail(self, id: str) -> List[Platform]:
        pass


class Direction(Enum):
    Forward = 'F'
    Back = 'B'


class Action(Enum):
    Form = 'F'
    Disband = 'D'
    Pass = 'P'


class TimetableEntry:
    train_id: str
    arrival: DT
    departure: DT
    cars: int
    direction: Direction
    action: Action

    def __init__(self, train_id: str, arrival: DT, departure: DT, cars: int, direction: Direction, action: Action):
        self.train_id = train_id
        self.arrival = arrival
        self.departure = departure
        self.cars = cars
        self.direction = direction
        self.action = action


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
    rail: Rail = None
    platform: Platform = None
    delay: int = 0

    def __init__(self, entry: TimetableEntry):
        self.entry = entry

    def schedule(self, rail: Rail, platform: Platform):
        self.rail = rail
        self.platform = platform


class TrainEvent(NamedTuple):
    ts: int
    train_id: str
    platform_id: str
    rail_id: str
    train_state: TrainState

    def __repr__(self) -> str:
        return ', '.join(map(str, ([self.ts, self.train_id, self.train_state, self.rail_id, self.platform_id])))

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o)


class StationState:
    transition_processors: Dict[Tuple[TrainState, TrainState], Callable[[TimetableEntryState], None]]
    state_processors: Dict[TrainState, Callable[[TimetableEntryState], None]]
    ts: DT = -1
    station: Station
    timetable: Timetable
    entries: List[TimetableEntryState] = []
    events: List[TrainEvent] = []

    def __init__(self, station: Station):
        self.station = station
        self.state_processors = {
            TrainState.Unscheduled: self.process_unscheduled,
            TrainState.Scheduled: self.process_scheduled,
            TrainState.DelayedArrival: self.process_delayed_arrival,
            TrainState.Railed: self.process_railed,
            TrainState.BeingFormed: self.process_being_formed,
        }
        self.transition_processors = {
            (None, TrainState.Scheduled): self.transit_to_scheduled,
            (TrainState.Unscheduled, None): self.transit_from_unscheduled,
            (None, TrainState.Disbanded): self.leave_station,
            (None, TrainState.Departed): self.leave_station,
            (None, None): self.fire_event,
        }

    def add_timetable(self, timetable: Timetable):
        for entry in timetable.entries:
            self.entries.append(TimetableEntryState(entry))

    def step(self):
        self.ts = self.ts + 1
        for entry in filter(lambda t: not t.state.terminal(), self.entries):
            self.state_processors[entry.state](entry)

    def step_n(self, n: int):
        for i in range(n - self.ts):
            self.step()

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

    def available(self, rail: Rail, platform: Platform) -> bool:
        return True

    def process_unscheduled(self, entry: TimetableEntryState):
        if entry.entry.action == Action.Form:
            if entry.entry.arrival - self.ts <= 30:
                platform, rail = self.get_first_available(entry)
                entry.schedule(rail, platform)
                self.change_state(entry, TrainState.BeingFormed)
        elif entry.entry.arrival - self.ts <= 10:
            platform, rail = self.get_first_available(entry)
            if rail and platform:
                entry.schedule(rail, platform)
                self.change_state(entry, TrainState.Scheduled)
            else:
                self.change_state(entry, TrainState.DelayedArrival)

    def get_first_available(self, entry: TimetableEntryState) -> Tuple[Platform, Rail]:

        for platform in self.station.platforms.values():
            if entry.entry.cars <= platform.max_cars:
                rails: List[Rail] = self.station.get_rails_for_platform(platform.id)
                if rails:
                    return platform, rails[0]
        return None, None

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
            if entry.entry.action == Action.Disband:
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

    def reset_events(self):
        self.events.clear()

    def current_events(self) -> List[TrainEvent]:
        return self.events

    def fire_event(self, entry: TimetableEntryState):
        rail_id: RailId = None
        if entry.rail:
            rail_id = entry.rail.id
        platform_id: PlatformId = None
        if entry.platform:
            platform_id = entry.platform.id
        self.events.append(TrainEvent(self.ts, entry.entry.train_id, entry.state, rail_id, platform_id))
