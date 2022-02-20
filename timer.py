"""A simple timer class collecting and reporting runtime statistics.
"""

from typing import DefaultDict, List, Optional, cast

import collections
import math
import statistics
import threading
import time


class Timer:

    def __init__(self, quiet=False):
        self.quiet = quiet
        self.local = threading.local()
        self.local.start_time = 0.0
        self.local.last_time = 0.0
        self.records: DefaultDict[str, List[float]
                                  ] = collections.defaultdict(list)
        self.order: List[str] = []

    def start(self):
        self.local.start_time = time.time()
        self.local.last_time = time.time()

    def segment(self, name: str):
        now = time.time()
        assert self.local.last_time, "Use .start() first!"
        self._append(name, now - self.local.last_time)
        self.local.last_time = now
        if name not in self.order:
            self.order.append(name)


    def stop(self):
        now = time.time()
        assert self.local.start_time, "Use .start() first!"
        self._append("total", now - self.local.start_time)
        self.local.last_time = 0.0
        self.local.start_time = 0.0

    def _append(self, name:str, taken:float):
        if not self.quiet:
            print("%.2fs %s" % (taken, name))
        self.records[name].append(taken)

    def report(self):
        order = self.order
        if "total" in self.records and not "total" in order:
            order.append("total")
        for name in order:
            records = self.records[name]
            print("%s: [%s ... %s]\n\t%d calls\n\t%.2fs mean\n\t%.2fs stdev" % (
                name,
                " ".join("%.2fs," % (r) for r in records[:5]),
                ", ".join("%.2fs" % (r) for r in records[-5:]),
                len(records),
                statistics.mean(records),
                statistics.stdev(records) if len(records) > 1 else math.nan))


