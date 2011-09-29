# encoding=UTF-8
# Copyright © 2011 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
# Copyright © 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import errno
import os

from xdg import BaseDirectory as xdg

if os.name == 'nt':
    # On Windows, use the “Application Data” folder if XDG_CONFIG_HOME is
    # not set.
    if ('XDG_CONFIG_HOME' not in os.environ) and ('APPDATA' in os.environ):
        xdg.xdg_config_home = os.environ['APPDATA']

class Config(object):

    def __init__(self, resource, legacy_path=None):
        self._dirty = False
        self._data = {}
        self._resource = resource
        for directory in xdg.load_config_paths(resource):
            self._load(os.path.join(directory, '%s.conf' % resource))
        self._legacy_path = legacy_path
        if legacy_path is not None:
            self._load(legacy_path)
            self._dirty = True

    def read(self, key, default):
        return self._data.get(key, default)

    def stru(self, unic):
	    if isinstance(unic, str):
		    return unic
	    else:
		    return str(unic.encode("utf-8"))

    def read_list(self, key, default):
        defaultString = ''
        for d in default:
            defaultString += self.__stru(d).replace('\\', '\\\\').replace(',', '\\,') + ','
        if defaultString != '':
            defaultString = defaultString[:-1]
        res = self._data.get(key, defaultString)
        els = res.split(",")
        prev = ''
        nels = []
        for i in range(0, len(els)):
            if len(prev) != 0 and prev[-1] == '\\':
                nels[-1] += ',' + els[i]
            else:
                nels.append(els[i])
            prev = els[i]
        for i in range(0, len(nels)):
            nels[i] = nels[i].replace('\\,', ',').replace('\\\\', '\\') # TODO: D co w razie \\\\, \\\\\\ itp.?
        if nels == ['']:
            nels = []
        return nels

    def read_int(self, key, default):
        return int(self.read(key, default))

    def read_bool(self, key, default):
        return bool(self.read_int(key, default))

    def __setitem__(self, key, value):
        self._data[key] = value
        self._dirty = True

    def _load(self, path):
        try:
            file = open(path, 'r')
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                return
        try:
            for line in file:
                line = line.rstrip()
                try:
                    key, value = line.split('=', 1)
                except ValueError:
                    pass
                value = value.decode('UTF-8')
                self._data[key] = value
        finally:
            file.close()

    def flush(self):
        if not self._dirty:
            return
        directory = xdg.save_config_path(self._resource)
        path = os.path.join(directory, '%s.conf' % self._resource)
        tmp_path = path + '.tmp'
        file = open(tmp_path, 'w')
        try:
            for key, value in self._data.iteritems():
                if isinstance(value, unicode):
                    value = value.encode('UTF-8')
                file.write('%s=%s\n' % (key, value))
            file.flush()
            os.fsync(file.fileno())
        finally:
            file.close()
        if os.name != 'posix' and os.path.exists(path):
            # Atomic renames might be not supported.
            backup_path = path + '.bak'
            os.rename(path, backup_path)
            os.rename(tmp_path, path)
            os.remove(backup_path)
        else:
            os.rename(tmp_path, path)
        if self._legacy_path is not None:
            try:
                os.remove(self._legacy_path)
            except OSError, ex:
                if ex.errno != errno.ENOENT:
                    raise
        self._dirty = False

# vim:ts=4 sw=4 et
