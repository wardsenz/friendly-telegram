#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import collections
import itertools
try:
    import coloredlogs  # Optional support for https://pypi.org/project/coloredlogs
    import coloredlogs.converter  # To switch between ANSI and HTML colors
except ModuleNotFoundError:
    import html
    _formatter = logging.Formatter

    def _converter(s):
        return "<code>" + html.escape(s) + "</code>"
else:
    _formatter = coloredlogs.ColoredFormatter
    _converter = coloredlogs.converter.convert


class MemoryHandler(logging.Handler):
    """Keeps 2 buffers. One for dispatched messages. One for unused messages. When the length of the 2 together is capacity
       truncate to make them capacity together, first trimming handled then unused."""
    def __init__(self, target, capacity, error_capacity=None):
        super().__init__(0)
        self.target = target
        self.buffer = collections.deque()
        self.handledbuffer = collections.deque()
        self.errorbuffer = collections.deque()
        self.capacity = capacity
        self._buffer_capacity = capacity - (error_capacity or 0)
        self._error_capacity = error_capacity
        self.lvl = logging.WARNING  # Default loglevel

    def _isError(self, record):
        return record.levelno >= self.lvl and self.lvl >= 0

    def setLevel(self, level):
        self.acquire()
        self.lvl = level
        self.release()

    def setCapacity(self, capacity, error_capacity=None):
        self.acquire()
        self.capacity = capacity
        self._error_capacity = error_capacity
        self._buffer_capacity = buffer_capacity = capacity - (error_capacity or 0)
        while len(self.buffer) + len(self.handledbuffer) > buffer_capacity:
            popped = (self.handledbuffer or self.buffer).popleft()
            if self._isError(popped):
                self.errorbuffer.append(popped)
        if error_capacity is not None:
            while len(self.errorbuffer) > error_capacity:
                self.errorbuffer.popleft()
        self.release()

    def dump(self):
        """Return a list of logging entries"""
        self.acquire()
        try:
            return list(itertools.chain(self.errorbuffer, self.handledbuffer, self.buffer))
        finally:
            self.release()

    def dumps(self, lvl=0):
        """Return all entries of minimum level as list of strings"""
        return [self.formatRecord(record) for record in (self.dump()) if record.levelno >= lvl]

    def formatRecord(self, record):
        return _converter(self.target.format(record))

    def emit(self, record):
        self.acquire()
        try:
            if len(self.buffer) + len(self.handledbuffer) >= self._buffer_capacity:
                popped = (self.handledbuffer or self.buffer).popleft()
                if self._isError(popped):
                    self.errorbuffer.append(popped)
                    if self._error_capacity and len(self.errorbuffer) > self._error_capacity:
                        self.errorbuffer.popleft()
            self.buffer.append(record)
            if self._isError(record):
                for popped in self.buffer:
                    self.target.handle(popped)
                self.handledbuffer.extend(self.buffer)
                self.buffer.clear()
        finally:
            self.release()


def init(capacity=500):
    formatter = _formatter(logging.BASIC_FORMAT, "")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    memory_handler = MemoryHandler(handler, capacity)
    logging.getLogger().addHandler(memory_handler)
    logging.getLogger().setLevel(0)
    logging.captureWarnings(True)
    return memory_handler


def getMemoryHandler():
    return next(filter(lambda h: isinstance(h, MemoryHandler), logging.getLogger().handlers), None)
