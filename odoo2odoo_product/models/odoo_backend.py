# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models

from ..consumer import BINDINGS


class OdooBackend(models.Model):
    _inherit = 'odoo.backend'

    @api.multi
    def get_model_bindings(self):
        return BINDINGS
