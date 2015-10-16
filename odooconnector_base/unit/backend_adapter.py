# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
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

    def read(self, id):
        raise NotImplementedError

    def search(self, filters):
        raise NotImplementedError

    def search_record(self, *args, **kwargs):
        raise NotImplementedError

    def write(self, id, data, **kwargs):
        raise NotImplementedError

    def _call(self, method, data,
              object_id=None, model_name=None, fields=None, context=None):
        """ Call a external Odoo method

        :param method: name of the method to be called
        :param data: data to be used for the method call
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

            api = self.connector_env.api
            # if a context is given we update the api context
            # TODO(MJ): Use a contextmanager for context changing!
            if context:
                context_copy = dict(api.context)
                for k, v in context.iteritems():
                    api.context[k] = v

            # Get the model object to work with
            if not model_name:
                model_name = self.model.openerp_id._name

            _logger.debug('Adapter is using model "%s" for call', model_name)
            model_obj = api.get(model_name)

            if not object_id:
                result = getattr(model_obj, method)(data)
            else:
                m = getattr(model_obj, method)
                if fields:
                    result = m(object_id, data, fields=fields)
                else:
                    result = m(object_id, data)

            _logger.debug('Backend call result: {}'.format(result))

            # Reset the context to old values
            if context:
                for k, v in context_copy.iteritems():
                    api.context[k] = v
                for k, v in context.iteritems():
                    api.context.pop(k)

            return result

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
        model_name = kwargs.get('model_name', None)
        context = kwargs.get('context', None)
        return self._call('create', data,
                          model_name=model_name, context=context)

    def delete(self, *args, **kwargs):
        return self._call('delete', 'somearg')

    def read(self, id, **kwargs):
        model_name = kwargs.get('model_name', None)
        context = kwargs.get('context', None)
        fields = kwargs.get('fields', None)
        return self._call('read', id, model_name=model_name,
                          fields=fields, context=context)

    def search(self, filters, **kwargs):
        """ Search according filters and return list of ids """
        if not filters:
            filters = []
        if 'domain' in filters:
            if not filters['domain']:
                filters.pop('domain')
            else:
                filters = eval(filters['domain'])

        context = kwargs.get('context', None)
        model_name = kwargs.get('model_name', None)
        result = self._call('search', filters, model_name=model_name,
                            context=context)
        _logger.debug("External search found this ids: {}".format(result))

        return result

    def search_record(self, *args, **kwargs):
        return self._call('search_record', 'somearg')

    def write(self, object_id, data, **kwargs):
        model_name = kwargs.get('model_name', None)
        context = kwargs.get('context', None)
        return self._call('write', data,
                          object_id=object_id, model_name=model_name,
                          context=context)
