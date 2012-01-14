# encoding=UTF-8

# Copyright © 2009 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import gettext
import os
import sys

for dir in os.path.join(os.path.dirname(sys.argv[0]), 'locale'), None:
    try:
        _ = gettext.translation('maleks', dir).ugettext
        break
    except IOError:
        pass
else:
    def _(s):
        return unicode(s, "utf-8") # TODO: NOTE bo _ musi zawsze zwracac unicode (por. db.getWorksForEntry itp.)
del dir

try:
    _ = gettext.translation('maleks', os.path.join(os.path.dirname(sys.argv[0]), 'locale'), languages=['pl']).ugettext
except IOError:
    _ = gettext.translation('maleks', '/usr/local/bin/locale', languages=['pl']).ugettext

# Some dummy translations:
if False:
    _('page')
    _('column')
    _('region')
    _('para')
    _('line')
    _('word')
    _('char')
    _('bookmarks')

# vim:ts=4 sw=4 et
