# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import urlparse

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import ConnectorEnvironment

from ..unit.backend_adapter import CheckAuth, GenericAPIAdapter
from ..backend import odoo
from ..exceptions import O2OConnectionError

_logger = logging.getLogger(__name__)


def extract_url_data(url):
    url_data = urlparse.urlparse(url)
    return {
        'scheme': url_data.scheme,
        'hostname': url_data.hostname,
        'port': url_data.port or (url_data.scheme == 'https' and 443) or 80,
    }


class OdooBackend(models.Model):
    _name = 'odoo.backend'
    _description = u"Odoo Backend"
    _inherit = 'connector.backend'
    _backend_type = 'odoo'

    active = fields.Boolean(u"Active", default=True)
    version = fields.Selection(
        selection='select_versions', string=u"Version", required=True)
    location = fields.Char(u"Location", required=True)
    hostname = fields.Char(
        u"Hostname", compute=u'_compute_url_data', store=True)
    protocol = fields.Char(
        u"Protocol", compute='_compute_url_data', store=True)
    port = fields.Integer(
        u"Port", compute='_compute_url_data', store=True)
    database = fields.Char(u"Database", required=True)
    username = fields.Char(u"Username", required=True)
    password = fields.Char(u"Password", required=True)

    @api.multi
    @api.depends('location')
    def _compute_url_data(self):
        for backend in self:
            url_data = extract_url_data(backend.location)
            self.hostname = url_data['hostname']
            self.port = url_data['port']
            self.protocol = \
                url_data['scheme'] == 'https' and 'jsonrpc+ssl' or 'jsonrpc'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions. Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [
            ('8.0', '8.0'),
            ('9.0', '9.0'),
        ]

    @api.multi
    def _get_api_adapter(self):
        """Get an adapter to test the backend connection."""
        self.ensure_one()
        session = ConnectorSession(self._cr, self._uid, context=self._context)
        environment = ConnectorEnvironment(self, session, self._name)
        return environment.get_connector_unit(CheckAuth)

    @api.multi
    def check_auth(self):
        self.ensure_one()
        message = u"Check authentication on %s (%s)" % (
            self.name, self.location)
        try:
            self._get_api_adapter()
        except O2OConnectionError, exc:
            _logger.error(u"%s: %s", message, exc)
            raise UserError(u"Connection error, check logs for more details")
        _logger.info(u"%s: OK", message)
        raise UserError(u"Connection OK")

    @api.multi
    def get_model_bindings(self):
        """Return the mapping between the data models and their corresponding
        bindings involved in the synchronization. E.g.:

            {
                'product.uom.categ': 'odoo.product.uom.categ',
                'product.uom': 'odoo.product.uom',
                'product.template': 'odoo.product.template',
                'product.product': 'odoo.product.product',
            }

        This is used by the synchronizers to allow the import/export
        of a record.

        This method must be implemented.
        """
        raise NotImplementedError


@odoo
class GenericCheckAuth(CheckAuth, GenericAPIAdapter):
    _model_name = 'odoo.backend'
