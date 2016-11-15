# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


class O2OError(RuntimeError):
    pass


class O2OConnectionError(O2OError):
    pass
