# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class OdooBinding(models.AbstractModel):
    _name = 'odoo.binding'
    _inherit = 'external.binding'
    _description = 'Odoo Binding (Abstract)'

    backend_id = fields.Many2one(
        'odoo.backend', u"Odoo Backend",
        required=True, ondelete='restrict')
    external_odoo_id = fields.Integer(u"ID in the external Odoo")
    sync_date = fields.Datetime(
        u"Last Synchronization Date")
    updated_on = fields.Datetime(u"Last Update in the external Odoo")

    _sql_constraints = [
        ('backend_odoo_uniq', 'unique(backend_id, external_odoo_id)',
         'A binding already exists with the same external Odoo ID.'),
    ]
