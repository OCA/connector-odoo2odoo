# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class OdooBackend(models.Model):

    _inherit = 'odooconnector.backend'

    po2so_external_partner = fields.Many2one(
        comodel_name='res.partner',
        string='PO2SO: External Partner',
        help='If set, the partner in the purchase order will be replaced\
              with this partner.',
        domain=[('supplier', '=', 'True')]
    )

    po2so_default_backend = fields.Boolean(
        string='Default PO2SO export backend',
        help='Use this backend as default for the PO2SO process.'
    )
