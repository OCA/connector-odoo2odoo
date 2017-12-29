# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from contextlib import contextmanager
from datetime import datetime, timedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class OdooBackend(models.Model):
    """ Model for Odoo Backends """
    _name = 'odooconnector.backend'
    _description = 'Odoo Backend'
    _inherit = 'connector.backend'

    _backend_type = 'odoo'

    @api.model
    def _select_versions(self):
        """ Available versions for this backend """
        return [('100', 'Version 10.0.x'),]

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

    
#     export_backend_id = fields.Integer(
#         string='Backend ID in the external system',
#         help="""The backend id that represents this system in the external
#                 system."""
#     )

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
    def get_environment(self, binding_model_name, api=None):
        self.ensure_one()
        if not api:
            api = odoorpc.ODOO(self.hostname, 'jsonrpc', self.port)
            api.login(self.database, self.username, self.password)
            _logger.info('Created a new Odoo API instance')
        env = APIConnectorEnvironment(self, binding_model_name, api=api)
        return env

    @api.multi
    @job
    def import_batch(self, binding_model_name, filters=None):
        """ Prepare a batch import of records from CSV """
        self.ensure_one()
        connector_env = self.get_environment(binding_model_name)
        importer = connector_env.get_connector_unit(BatchImporter)
        importer.run(filters=filters)

    @api.multi
    @job
    def import_record(self, binding_model_name, ext_id, force=False, api=None):
        """ Import a record from CSV """
        self.ensure_one()
        connector_env = self.get_environment(binding_model_name)
        importer = connector_env.get_connector_unit(OdooImporter)
        importer.run(ext_id, force=force)

    @api.multi
    def import_partners(self):
        """ Import partners from external system """
        for backend in self:
            filters = self.import_partner_domain_filter
            if filters and isinstance(filters, str):
                filters = eval(filters)

            backend.import_batch('odooconnector.res.partner', filters)

        return True

    @api.multi
    def import_products(self):
        """ Import products from external system """
        for backend in self:
            filters = self.import_product_domain_filter
            if filters and isinstance(filters, str):
                filters = eval(filters)

            backend.import_batch('odooconnector.product.product', filters)

        return True

    @api.multi
    def import_product_uom(self):
        """Import Product UoM from external System"""
        for backend in self:
            backend.import_batch('odooconnector.product.uom')
return True