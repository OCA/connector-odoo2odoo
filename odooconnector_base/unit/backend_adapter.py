# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

try:
    import oerplib.error
except ImportError:
    pass

from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from ..backend import oc_odoo

_logger = logging.getLogger(__name__)


class OdooAdapterGeneric(CRUDAdapter):

    def __init__(self, connector_env):
        super(OdooAdapterGeneric, self).__init__(connector_env)
        # TODO(MJ): Change log level to debug after load test
        _logger.info('Backend adapter initialised')

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def read(self, id, **kwargs):
        raise NotImplementedError

    def search(self, filters, **kwargs):
        raise NotImplementedError

    def write(self, id, data, **kwargs):
        raise NotImplementedError

    def _get_api_model(self, model_name=None):
        """ Get the API model object to work with """
        if not model_name:
            model_name = self.model.openerp_id._name

        _logger.debug('Adapter is using model "%s" for call', model_name)
        return self.api.get(model_name)

    def _api_reset_context(self, old_context, new_context):
        """ Reset the APIs context to the old_context """
        for k, v in new_context.iteritems():
            self.api.context.pop(k)
        for k, v in old_context.iteritems():
            self.api.context[k] = v

    def _call(self, method, data,
              object_id=None, model_name=None, fields=None, context=None):
        """ Call a external Odoo method

        :param method: name of the method to be called
        :param data: data to be used for the method call
        :param object_id: id of the object in the remote system
        :param model_name: define a specific model on which the method should
                           be called.
        :param context: custom context in which the query must be executed.
                        E.g. for setting a different language.
                        Only the fields given in the context dict are replaced
                        in the connection context.
        :types context: dict
        """

        _logger.debug('Adapter method call: "{}" with data "{}"'.format(
                      method, data))
        _logger.debug('Adapter is using backend_record "%s:%s"',
                      self.backend_record, self.backend_record.name)
        try:
            self.api = self.connector_env.api

            # if a context is given we update the api context
            # TODO(MJ): Use a contextmanager for context changing!
            if context:
                org_context = dict(self.api.context)
                for k, v in context.iteritems():
                    self.api.context[k] = v

            model_obj = self._get_api_model(model_name)

            if not object_id:
                result = getattr(model_obj, method)(data)
            else:
                m = getattr(model_obj, method)
                if fields:
                    result = m(object_id, data, fields=fields)
                else:
                    result = m(object_id, data)

            _logger.debug('Backend call result: {}'.format(result))

            if context:
                self._api_reset_context(org_context, context)

            return result

        except oerplib.error.RPCError as e:
            _logger.exception(e)

        except Exception as e:
            _logger.exception(e)


@oc_odoo
class OdooAdapter(OdooAdapterGeneric):

    _model_name = ['odooconnector.res.partner',
                   'odooconnector.product.product',
                   'odooconnector.product.uom',
                   'odooconnector.product.supplierinfo',
                   'pricelist.partnerinfo',
                   'product.uom'
                   ]

    def create(self, data, **kwargs):
        # model_name = kwargs.get('model_name', None)
        # context = kwargs.get('context', None)
        return self._call('create', data, **kwargs)

    def delete(self, *args, **kwargs):
        return self._call('delete', 'somearg')

    def read(self, id, **kwargs):
        # model_name = kwargs.get('model_name', None)
        # context = kwargs.get('context', None)
        # fields = kwargs.get('fields', None)
        return self._call('read', id, **kwargs)

    def search(self, filters, **kwargs):
        """ Search according filters and return list of ids """
        if not filters:
            filters = []

        # context = kwargs.get('context', None)
        # model_name = kwargs.get('model_name', None)
        result = self._call('search', filters, **kwargs)
        _logger.debug("External search found this ids: {}".format(result))

        return result

    def write(self, object_id, data, **kwargs):
        # model_name = kwargs.get('model_name', None)
        # context = kwargs.get('context', None)
        return self._call('write', data,
                          object_id=object_id, **kwargs)
