# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import openerp.tests.common as common

from openerp.addons.connector.session import ConnectorSession


class SetUpOdooBase(common.TransactionCase):
    """Base class to test the backend."""

    def setUp(self):
        super(SetUpOdooBase, self).setUp()
        self.session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        self.backend = self.env.ref('odoo2odoo_backend.odoo_backend_default')
        self.backend.write({
            'active': True,
            'location': 'http://localhost:8069/',
            'database': self.env.cr.dbname,
        })
