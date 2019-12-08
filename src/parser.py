from typing import List

from src.main import Station, Rail, Platform, Timetable, TimetableEntry


def build(filename: str) -> (Station, Timetable):
    station = Station()
    entries: List[TimetableEntry] = list()
    with open(filename, "rt") as fp:
        for line in fp:
            t = line[0]
            s = list(map(lambda ss: ss.strip(), line[2:-1].split(",")))
            if t == 'R':
                station.add_rail(Rail(s[0]))
            elif t == 'P':
                station.add_platform(Platform(s[0], int(s[1])))
            elif t == 'L':
                station.add_link(s[0], s[1])
            elif t == 'T':
                entries.append(TimetableEntry(int(s[0]), int(s[1]), int(s[2])))
    (station, Timetable(entries))
