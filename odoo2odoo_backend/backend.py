# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import openerp.addons.connector.backend as backend


odoo = backend.Backend('odoo')
"""Generic Odoo Backend"""

odoo80 = backend.Backend(parent=odoo, version='8.0')
"""Odoo Backend for version 8.0"""

odoo90 = backend.Backend(parent=odoo, version='9.0')
"""Odoo Backend for version 9.0"""
