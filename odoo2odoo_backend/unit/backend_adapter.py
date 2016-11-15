# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import urllib2

_logger = logging.getLogger(__name__)

try:
    import odoorpc
except ImportError:
    _logger.debug('Cannot `import odoorpc`.')

from openerp.addons.connector.unit.backend_adapter \
    import BackendAdapter, CRUDAdapter

from ..exceptions import O2OConnectionError


class CheckAuth(BackendAdapter):
    pass


class GenericAPIAdapter(BackendAdapter):
    """Generic class to open a session on the external Odoo server."""

    def __init__(self, connector_env):
        super(GenericAPIAdapter, self).__init__(connector_env)
        self.odoo_session = self.get_odoo_session()

    def get_odoo_session(self):
        """Returns an OdooRPC session to perform RPC requests.

        :return: a OdooRPC user session
        :rtype: ``odoorpc.ODOO``
        """
        try:
            client = odoorpc.ODOO(
                self.backend_record.hostname,
                protocol=self.backend_record.protocol,
                port=int(self.backend_record.port),
                version=self.backend_record.version)
            client.login(
                self.backend_record.database,
                self.backend_record.username,
                self.backend_record.password)
            client.env.context.clear()
            _logger.info(
                "%s - Session open for user %s",
                self.backend_record.name,
                self.backend_record.username)
            return client
        except odoorpc.error.RPCError as exc:
            _logger.error(exc)
            raise O2OConnectionError(exc)           # e.g 401
        except urllib2.URLError as exc:
            _logger.error(exc)
            raise O2OConnectionError(exc.reason)    # e.g unreachable, timeout


    def execute(self, method, *args, **kwargs):
        binder = self.binder_for(self.model._name)
        model_name = self.model.fields_get(
            [binder._openerp_field])[binder._openerp_field]['relation']
        log = {
            'model': model_name,
            'method': method,
            'args': args,
            'kwargs': kwargs,
        }
        #try:
        _logger.info("%s - %s", self.backend_record.name, log)
        odoo_model = self.odoo_session.env[model_name]
        return getattr(odoo_model, method)(*args, **kwargs)
        # except urllib2.HTTPError, exc:
        #     _logger.error(exc)
        #     raise


class GenericCRUDAdapter(GenericAPIAdapter, CRUDAdapter):
    """External Records Adapter for Odoo."""

    def search(self, *args, **kwargs):
        """Search documents on the external Odoo according to some criterias
        and returns a list of UIDs.

        Usage::

            >>> self.backend_adapter.search(
            ...    [('is_company', '=', True)], limit=4)
            [1, 3, 4, 7]
        """
        return self.execute('search', *args, **kwargs)

    def read(self, *args, **kwargs):
        """Returns the information of a record from the external Odoo server.
        """
        return self.execute('read', *args, **kwargs)

    def search_read(self, *args, **kwargs):
        return self.execute('search_read', *args, **kwargs)

    def create(self, *args, **kwargs):
        return self.execute('create', *args, **kwargs)

    def write(self, *args, **kwargs):
        return self.execute('write', *args, **kwargs)

    def unlink(self, *args, **kwargs):
        return self.execute('unlink', *args, **kwargs)

    # Use of low-level CRUD methods added by the 'odoo2odoo_node' module

    def raw_read(self, *args, **kwargs):
        """Returns the information of a record from the external Odoo server.
        """
        return self.execute('o2o_read', *args, **kwargs)

    def raw_create(self, *args, **kwargs):
        return self.execute('o2o_create', *args, **kwargs)

    def raw_write(self, *args, **kwargs):
        return self.execute('o2o_write', *args, **kwargs)

    def raw_unlink(self, *args, **kwargs):
        return self.execute('o2o_unlink', *args, **kwargs)
