# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api
from openerp.addons.connector.session import ConnectorSession
from ..unit.import_synchronizer import import_batch


class IntercompanyBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Odoo and OdooIC should inherit it.
    """
    _name = 'intercompany.binding'
    _inherit = 'external.binding'
    _description = 'Intercompany Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='intercompany.backend',
        string='Intercompany Backend',
        required=False,
        ondelete='restrict',
    )

    intercompany_id = fields.Integer(
        string='ID in OdooIC System'
    )

    exported_record = fields.Boolean(
        string='Exported',
        help='Indicator if the record is exported by this system or not.',
        default=False,
    )

    _sql_constraints = [
        ('odooic_uniq', 'unique(backend_id, intercompany_id)',
         'A binding already exists with the same IC ID.'),
    ]


class IntercompanyBackend(models.Model):
    """ Model for Odoo Intercompany Backends """
    _name = 'intercompany.backend'
    _description = 'Intercompany Backend'
    _inherit = 'connector.backend'

    _backend_type = 'odoo'

    @api.model
    def _select_versions(self):
        """ Available versions for this backend """
        return [('700', 'Version 7.00'),
                ('800', 'Version 8.00'),
                ('900', 'Version 9.00')]

    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )

    username = fields.Char(
        string='Username',
        required=True,
        help='Username in the Odoo Intercompany Backend'
    )
    password = fields.Char(
        string='Password',
        required=True,
        help='Password'
    )
    database = fields.Char(string='Database', required=True)
    hostname = fields.Char(string='Hostname', required=True)
    port = fields.Integer(string='Port', required=True)

    import_partner_from_date = fields.Datetime(
        string='Import parterns from date',
        readonly=True
    )

    import_partner_domain_filter = fields.Char(
        string='Import partner domain filter',
    )

    import_product_domain_filter = fields.Char(
        string='Import product domain filter',
    )

    export_backend_id = fields.Integer(
        string='Export: Id of the backend in the IC system',
        help="""The backend id that represents this system in the intercompany
                system """
    )

    export_partner_id = fields.Integer(
        string='Export: Our Partner ID in the Intercompany System',
        help="""The partner id that represents this company in the
                intercompany system"""
    )

    export_purchase_order_default_location_id = fields.Integer(
        string='Export: Default location ID for POs'
    )

    export_purchase_order_default_pricelist_id = fields.Integer(
        string='Export: Default pricelist ID for POs'
    )

    po2so_intercompany_partner = fields.Many2one(
        comodel_name='res.partner',
        string='PO2SO: Intercompany Partner',
        help='If set, the partner in the purchase order will be replaced\
              with this partner.',
        domain=[('supplier', '=', 'True')]
    )

    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language'
    )

    default_po2so_backend = fields.Boolean(
        string='Default PO2SO export backend',
        help='Use this backend as default for the PO2SO process.'
    )

    default_export_backend = fields.Boolean(
        string='Default Export Intercompany Backend',
        help='Use this backend as an automatic export targed'
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
        """ Import partners from Intercompany System """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for backend in self:
            filters = {
                'domain': self.import_partner_domain_filter,
            }
            import_batch(session, 'intercompany.res.partner', backend.id,
                         filters)

        return True

    @api.multi
    def import_products(self):
        """ Import products from Intercompany System """
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)

        for backend in self:
            filters = {
                'domain': self.import_product_domain_filter,
            }
            import_batch(session, 'intercompany.product.product',
                         backend.id, filters)

        return True

    @api.multi
    def import_product_uom(self):
        """Import Product UoM from Intercompany System"""
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)

        for backend in self:
            import_batch(session, 'intercompany.product.uom', backend.id)
        return True
