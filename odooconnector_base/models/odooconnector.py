# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api
from openerp.addons.connector.session import ConnectorSession

from ..unit.import_synchronizer import import_batch


class OdooBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Odoo and OdooIC should inherit it.
    """
    _name = 'odooconnector.binding'
    _inherit = 'external.binding'
    _description = 'Odoo Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='odooconnector.backend',
        string='Odoo Backend',
        required=False,
        ondelete='restrict',
    )

    external_id = fields.Integer(
        string='ID in external Odoo system'
    )

    exported_record = fields.Boolean(
        string='Exported',
        help='Indicator whether the record is exported by this system or not.',
        default=False,
    )

    _sql_constraints = [
        ('external_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same external ID.'),
    ]


class OdooBackend(models.Model):
    """ Model for Odoo Backends """
    _name = 'odooconnector.backend'
    _description = 'Odoo Backend'
    _inherit = 'connector.backend'

    _backend_type = 'odoo'

    @api.model
    def _select_versions(self):
        """ Available versions for this backend """
        return [('700', 'Version 7.00'),
                ('800', 'Version 8.00'),
                ('900', 'Version 9.00')]

    active = fields.Boolean(
        string='Active',
        default=True
    )

    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )

    username = fields.Char(
        string='Username',
        required=True,
        help='Username in the external Odoo Backend.'
    )
    password = fields.Char(
        string='Password',
        required=True,
    )
    database = fields.Char(string='Database', required=True)
    hostname = fields.Char(string='Hostname', required=True)
    port = fields.Integer(string='Port', required=True)

    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language'
    )

    import_partner_domain_filter = fields.Char(
        string='Partner domain filter',
    )

    import_product_domain_filter = fields.Char(
        string='Product domain filter',
    )

    export_backend_id = fields.Integer(
        string='Backend ID in the external system',
        help="""The backend id that represents this system in the external
                system."""
    )

    export_partner_id = fields.Integer(
        string='Partner ID in the external System',
        help="""The partner id that represents this company in the
                external system."""
    )

    default_export_backend = fields.Boolean(
        string='Default Export Backend',
        help='Use this backend as an automatic export target.'
    )

    default_export_partner = fields.Boolean(
        string='Export Partners'
    )

    default_export_partner_domain = fields.Char(
        string='Export Partners Domain',
        default='[]'
    )

    default_export_product = fields.Boolean(
        string='Export Products'
    )

    default_export_product_domain = fields.Char(
        string='Export Products Domain',
        default='[]'
    )

    @api.multi
    def import_partners(self):
        """ Import partners from external system """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for backend in self:
            filters = self.import_partner_domain_filter
            if filters and isinstance(filters, str):
                filters = eval(filters)

            import_batch(session, 'odooconnector.res.partner', backend.id,
                         filters)

        return True

    @api.multi
    def import_products(self):
        """ Import products from external system """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)

        for backend in self:
            filters = self.import_product_domain_filter
            if filters and isinstance(filters, str):
                filters = eval(filters)

            import_batch(session, 'odooconnector.product.product',
                         backend.id, filters)

        return True

    @api.multi
    def import_product_uom(self):
        """Import Product UoM from external System"""
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)

        for backend in self:
            import_batch(session, 'odooconnector.product.uom', backend.id)
        return True
