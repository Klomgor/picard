# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Yvan Rivière
# Copyright (C) 2018, 2020-2021, 2024 Laurent Monin
# Copyright (C) 2018, 2020-2022 Philipp Wolfer
# Copyright (C) 2024 Yohay
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from functools import partial

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.album import Album
from picard.cluster import (
    Cluster,
    ClusterList,
)
from picard.i18n import N_
from picard.script import (
    ScriptError,
    ScriptParser,
)
from picard.track import Track
from picard.util import iter_unique


class ScriptsMenu(QtWidgets.QMenu):

    def __init__(self, scripts, title, parent=None):
        super().__init__(title, parent=parent)
        self.tagger = QtCore.QCoreApplication.instance()

        for script in scripts:
            action = self.addAction(script.name)
            action.triggered.connect(partial(self._run_script, script))

    def _run_script(self, script):
        parser = ScriptParser()

        for obj in self._iter_unique_metadata_objects():
            try:
                parser.eval(script.content, obj.metadata)
                obj.update()
            except ScriptError as e:
                log.exception('Error running tagger script "%s" on object %r', script.name, obj)
                msg = N_('Script error in "%(script)s": %(message)s')
                mparms = {
                    'script': script.name,
                    'message': str(e),
                }
                self.tagger.window.set_statusbar_message(msg, mparms)

    def _iter_unique_metadata_objects(self):
        return iter_unique(self._iter_metadata_objects(self.tagger.window.selected_objects))

    def _iter_metadata_objects(self, objs):
        for obj in objs:
            if hasattr(obj, 'metadata') and not getattr(obj, 'special', False):
                yield obj
            if isinstance(obj, Cluster) or isinstance(obj, Track):
                yield from self._iter_metadata_objects(obj.iterfiles())
            elif isinstance(obj, ClusterList):
                yield from self._iter_metadata_objects(obj)
            elif isinstance(obj, Album):
                yield from self._iter_metadata_objects(obj.tracks)
                yield from self._iter_metadata_objects(obj.unmatched_files.iterfiles())
