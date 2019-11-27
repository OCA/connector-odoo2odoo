# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import fields, models
from openerp.addons.connector.connector import Binder
from ..backend import oc_odoo

_logger = logging.getLogger(__name__)


@oc_odoo
class OdooModelBinder(Binder):
    _model_name = [
        'odooconnector.res.partner',
        'odooconnector.product.product',
        'odooconnector.product.supplierinfo',
        'odooconnector.product.uom',
    ]

    def to_openerp(self, external_id, unwrap=False, browse=False):
        """ Return the Odoo ID for an external ID

        :param unwrap: if True, returns the normal record (the one
                       inherits'ed), else return the binding record
        :param browse: if True, returns a recordset
        :return: a recordset of one record, depending on the value of unwrap,
                 or an empty recordset if no binding is found
        """
        _logger.debug('Binder: to_openerp')
        bindings = self.model.with_context(active_test=False).search(
            [('external_id', '=', external_id),
             ('backend_id', '=', self.backend_record.id)]
        )

        if not bindings:
            return self.model.browse() if browse else None

        assert len(bindings) == 1, "Several records found: %s" % bindings

        if unwrap:
            return bindings.openerp_id if browse else bindings.openerp_id.id
        else:
            return bindings if browse else bindings.id

    def to_backend(self, binding_id, wrap=False):
        """ Give the external ID for an OpenERP binding ID

        :param binding_id: OpenERP binding ID for which we want the backend id
        :param wrap: if False, binding_id is the ID of the binding,
                     if True, binding_id is the ID of the normal record, the
                     method will search the corresponding binding and returns
                     the backend id of the binding
        :return: external ID of the record
        """
        _logger.debug('Binder: to_backend')
        if wrap:
            binding = self.model.with_context(active_test=False).search(
                [('openerp_id', '=', binding_id),
                 ('backend_id', '=', self.backend_record.id)]
            )
            if binding:
                binding.ensure_one()
                return binding.external_id
            else:
                return None

        record = self.model.browse(binding_id)
        assert record
        return record.external_id

    def bind(self, external_id, binding_id, exported=False):
        """ Create the link between an external ID and an OpenERP ID
        :param external_id: external id to bind
        :param binding_id: OpenERP ID to bind
        :type binding_id: int
        """
        _logger.debug('Binder: bind')
        now_fmt = fields.Datetime.now()
        if not isinstance(binding_id, models.BaseModel):
            binding_id = self.model.browse(binding_id)

        data = {'external_id': external_id,
                'sync_date': now_fmt}

        if exported:
            data['exported_record'] = True

        binding_id.with_context(connector_no_export=True).write(data)

    def unwrap_binding(self, binding_id, browse=False):
        """ For a binding record, gives the normal record.
        Example: when called with a ``magento.product.product`` id,
        it will return the corresponding ``product.product`` id.
        :param browse: when True, returns a browse_record instance
        rather than an ID
        """
        if isinstance(binding_id, models.BaseModel):
            binding = binding_id
        else:
            binding = self.model.browse(binding_id)

        record = binding.openerp_id
        if browse:
            return record
        else:
            return record.id

    def unwrap_model(self):
        """ For a binding model, gives the normal model.
        Example: when called on a binder for ``magento.product.product``,
        it will return ``product.product``.
        """
        raise NotImplementedError
