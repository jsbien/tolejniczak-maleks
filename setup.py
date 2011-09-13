#!/usr/bin/python
# encoding=UTF-8
# Copyright © 2008, 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2011 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''
*maleks* is a tool for managing lexicographic data.
'''

classifiers = '''
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Topic :: Text Processing
Topic :: Multimedia :: Graphics
'''.strip().split('\n')

import glob
import os

import distutils.core
from distutils.command.build import build as distutils_build
from distutils.command.sdist import sdist as distutils_sdist

from lib import __version__

os.putenv('TAR_OPTIONS', '--owner root --group root --mode a+rX')

data_files = []
for root, dirs, files in os.walk('locale'):
    for f in files:
        if not f.endswith('.mo'):
            continue
        data_files.append(
            (os.path.join('share', root),
            [os.path.join(root, f)]
        ))
manpages = set()
data_files = [('share/man/man1', manpages), ('share/maleks/res', ['res/binary.png', 'res/chreg.png', 'res/edins.png', 'res/edpre.png', 'res/hins.png', 'res/next.png', 'res/prev.png', 'res/up.png', 'res/back.png', 'res/defreg.png'])]

class build_doc(distutils_build):

    description = 'build documentation'

    def run(self):
        if os.name != 'posix':
            return
        for xmlname in glob.glob(os.path.join('doc', '*.xml')):
            manname = os.path.splitext(xmlname)[0] + '.1'
            command = [
                'xsltproc', '--nonet',
                '--param', 'man.charmap.use.subset', '0',
                '--output', 'doc/',
                'http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl',
                xmlname,
            ]
            self.make_file([xmlname], manname, distutils.spawn.spawn, [command])
            manpages.add(manname)

distutils_build.sub_commands[:0] = [('build_doc', None)]

class sdist(distutils_sdist):

    def run(self):
        self.run_command('build_doc')
        return distutils_sdist.run(self)

distutils.core.setup(
    name = 'maleks',
    version = __version__,
    license = 'GNU GPL 2',
    description = 'lexicographic data tool',
    long_description = __doc__.strip(),
    classifiers = classifiers,
    url = '',
    author = 'Tomasz Olejniczak',
    author_email = 'tomek.87@poczta.onet.pl',
    packages = ['maleks'] + ['maleks.%s' % x for x in 'db gui models text maleks'.split()],
    package_dir = dict(maleks='lib'),
    scripts = ['maleks'],
    data_files = data_files,
    cmdclass = dict(
        sdist=sdist,
        build_doc=build_doc,
    ),
)

# vim:ts=4 sw=4 et
