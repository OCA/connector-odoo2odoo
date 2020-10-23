# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from contextlib import contextmanager
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.connector_odoo.components.backend_adapter import OdooLocation, OdooAPI
# from vminstall.msg import protocol

_logger = logging.getLogger(__name__)

class OdooBackend(models.Model):
    """ Model for Odoo Backends """
    _name = 'odoo.backend'
    _description = 'Odoo Backend'
    _inherit = 'connector.backend'

    _backend_type = 'odoo'


    @api.model
    def _select_state(self):
        """Available States for this Backend"""
        return [('draft', 'Draft'),
                ('checked', 'Checked'),
                ('production', 'In Production'),]
        
    @api.model
    def _select_versions(self):
        """ Available versions for this backend """
        return [('10.0', 'Version 10.0.x'),]

    active = fields.Boolean(
        string='Active',
        default=True
    )
    state = fields.Selection(
        selection='_select_state',
        string='State',
        default='draft'
    )
    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    login = fields.Char(
        string='Username / Login',
        required=True,
        help='Username in the external Odoo Backend.'
    )
    password = fields.Char(
        string='Password',
        required=True,
    )
    database = fields.Char(string='Database', required=True)
    hostname = fields.Char(string='Hostname', required=True)
    port = fields.Integer(
        string='Port', 
        required=True,
        help="For SSL, 443 is mostly the right choice",
        default=8069
        )

    protocol = fields.Selection(
        selection=[('jsonrpc', 'JsonRPC'),
                   ('jsonrpc+ssl', 'JsonRPC with SSL')],
        string='Protocol',
        required=True,
        default='jsonrpc',
        help="For SSL, consider changing the port to 443 is mostly the right choice",
        
    )
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
    def _check_connection(self):
        self.ensure_one()
        odoo_location = OdooLocation(
            hostname=self.hostname,
            login=self.login,
            password=self.password,
            database=self.database,
            port=self.port,
            version=self.version,
            protocol=self.protocol
        )
        odoo_api =  OdooAPI(odoo_location)
        odoo_api.complete_check()        
        self.write({'state': 'checked'})
        

    @api.multi
    def button_check_connection(self):
        self._check_connection()

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        
    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        """
        Place the connexion here regarding the documentation
        http://odoo-connector.com/api/api_components.html#odoo.addons.component.models.collection.Collection
        """
        self.ensure_one()
        lang = self.default_lang_id
        if lang.code != self.env.context.get('lang'):
            self = self.with_context(lang=lang.code)
        odoo_location = OdooLocation(
            hostname=self.hostname,
            login=self.login,
            password=self.password,
            database=self.database,
            port=self.port,
            version=self.version,
            protocol=self.protocol,
            lang_id=self.default_lang_id.code     
        )
        with OdooAPI(odoo_location) as odoo_api:
            _super = super(OdooBackend, self)
            # from the components we'll be able to do: self.work.magento_api
            with _super.work_on(
                    model_name, odoo_api=odoo_api, **kwargs) as work:
                yield work



    @api.multi
    def synchronize_basedata(self):
        try:
            for backend in self:
                for model_name in ('odoo.product.uom',
#                                    'odoo.product.category',
                                    'odoo.product.attribute',
                                    'odoo.product.attribute.value'
                                   ):
                    # import directly, do not delay because this
                    # is a fast operation, a direct return is fine
                    # and it is simpler to import them sequentially
                    self.env[model_name].import_batch(backend)
            return True
        except Exception as e:
            _logger.error(e.message, exc_info=True)
            raise UserError(
                _(u"Check your configuration, we can't get the data. "
                  u"Here is the error:\n%s") %
                str(e).decode('utf-8', 'ignore'))

  