# -*- coding: utf-8 eval: (blacken-mode 1) -*-
#
# December 4 2022, Christian Hopps <chopps@labn.net>
#
# Copyright (c) 2022, LabN Consulting, L.L.C.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; see the file COPYING; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
"Utilities for logging in munet"

import logging

from pathlib import Path


class MultiFileHandler(logging.FileHandler):
    """A logging handler that logs to new files based on the logger name.

    The MultiFileHandler operates as a FileHandler with additional
    functionality. In addition to logging to the specified logging file
    MultiFileHandler also creates new FileHandlers for child loggers
    based on a root logging name path.

    The ``root_path`` determines when to create a new FileHandler. For each
    received log record, ``root_path`` is removed from the logger name and the
    resulting path name (if any) determines the log file to also emit the
    record to. The path of the new logfile is determined by converting "." to
    "/" and appending ".log" to the final compoenent (the filename) it is
    opened relative to the directory for the common base filename.

    For example: "<rootpath>.server1.output" would become "server1/output.log"
    and if filename was "/tmp/unet-mutest/output.log" the full path to
    the new FileHandler would be "/tmp/unet-mutest/server1/output.log"

    All messages are also emitted to the common FileLogger for ``filename``.

    If a log record is from a logger that does not start with ``root_path``
    no file is created and the normal emit occurs.

    Args:
        root_path: the logging path of the root level for this handler.
        log_dir: the log directory to put log files in.
        filename: the base log file.
    """

    def __init__(self, root_path, filename=None, **kwargs):
        self.__root_path = root_path
        if root_path[-1] != ".":
            self.__root_path += "."
        self.__root_pathlen = len(self.__root_path)
        self.__kwargs = kwargs
        self.__log_dir = Path(filename).absolute().parent
        self.__log_dir.mkdir(parents=True, exist_ok=True)
        self.__filenames = {}
        self.__added = set()
        super().__init__(filename=filename, **kwargs)

    def __log_filename(self, name):
        if name in self.__filenames:
            return self.__filenames[name]

        if not name.startswith(self.__root_path):
            newname = None
        else:
            newname = name[self.__root_pathlen :]
            newname = newname.replace(".", "/") + ".log"
            newname = self.__log_dir.joinpath(newname)
            self.__filenames[name] = newname

        self.__filenames[name] = newname
        return newname

    def emit(self, record):
        newname = self.__log_filename(record.name)
        if newname:
            if newname not in self.__added:
                self.__added.add(newname)
                h = logging.FileHandler(filename=newname, **self.__kwargs)
                logging.getLogger(record.name).addHandler(h)
                h.emit(record)
        super().emit(record)
