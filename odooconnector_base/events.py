# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp.addons.connector.event import on_record_write, on_record_create

from .unit.export_synchronizer import export_record


_logger = logging.getLogger(__name__)

# Some patching of the original write / create events:
# This is a security mechanism to prevent cyclic export processes
original_fire_create = on_record_create.fire
original_fire_write = on_record_write.fire


# TODO(MJ): Patching should be done on install, not on import!
def new_fire(original):
    def new_fire(self, session, model_name, *args, **kwargs):
        config_obj = self.env['ir.config_parameter']
        export = config_obj.get_param('odooconnector.export_sync') or None
        # TODO(MJ): Must be changed!
        if export and eval(export):
            original(self, session, model_name, *args, **kwargs)
        else:
            _logger.debug('Did not fire "%s"' % original)
    return new_fire


on_record_create.fire = new_fire(original_fire_create)
on_record_write.fire = new_fire(original_fire_write)


@on_record_create(model_names=['odooconnector.product.product',
                               'odooconnector.res.partner'])
def export_odooconnector_object(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return

    _logger.debug('Record creation triggered for "%s(%s)"',
                  model_name, record_id)
    sync_object(session, model_name, record_id, fields)


@on_record_create(model_names=['product.product',
                               'res.partner'])
def create_default_binding(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record creation triggered for "%s(%s)"',
                  model_name, record_id)

    obj = session.env[model_name].browse(record_id)

    default_backends = session.env['odooconnector.backend'].search(
        [('default_export_backend', '=', True)]
    )

    ic_model_name = 'odooconnector.' + model_name
    for backend in default_backends:
        _logger.debug('Create binding for default backend %s', backend.name)
        session.env[ic_model_name].create({
            'backend_id': backend.id,
            'openerp_id': obj.id,
            'exported_record': True
        })


# TODO(MJ): At this time, if product.template and product.product fields get
#           changed in the same transaction (e.g. in the product view), two
#           export jobs will be created: one for product.template and one for
#           product.product. If you have more than one export backend, this
#           gets even multiplied by the amount of backends: 2 backends means
#           4 export jobs. So far I have no idea how to deal with this!
@on_record_write(model_names=['product.product', 'product.template'])
def update_product(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

    # In the procedure of creating a new product.template this check prevents
    # creating redundant export jobs
    if not fields:
        _logger.debug('Sync skipped for "%s(%s) [No fields]"',
                      model_name, record_id)
        return
    else:
        ic_model_name = 'odooconnector.product.product'
        bindings = []

        if model_name == 'product.template':
            fields = {}  # product.template fields are not compatible with p.p
            obj = session.env['product.template'].browse(record_id)
            for product in obj.product_variant_ids:
                for binding in product.ic_bind_ids:
                    bindings.append(binding)

        else:
            model_name = 'odooconnector.product.product'
            obj = session.env['product.product'].browse(record_id)
            bindings = obj.oc_bind_ids

        for binding in bindings:
            _logger.debug('Sync process start for "%s(%s)"',
                          model_name, binding.id)
            sync_object(session, ic_model_name, binding.id, fields)


@on_record_write(model_names=['res.partner'])
def update_partner(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    _logger.debug('Record write triggered for %s(%s)', model_name, record_id)

    # In the procedure of creating a new product.template this check prevents
    # creating redundant export jobs
    if not fields:
        _logger.debug('Sync skipped for "%s(%s) [No fields]"',
                      model_name, record_id)
        return
    else:
        ic_model_name = 'odooconnector.' + model_name
        obj = session.env[model_name].browse(record_id)

        for binding in obj.oc_bind_ids:
            _logger.debug('Sync process start for "%s(%s)"',
                          model_name, binding.id)
            sync_object(session, ic_model_name, binding.id, fields)


def sync_object(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    obj = session.env[model_name].search([('id', '=', record_id)])
    if obj:
        _logger.debug('Sync record')
        export_record.delay(session, model_name, obj.backend_id.id, record_id)
    else:
        _logger.debug('Sync skipped for %s(%s) [No binding]',
                      model_name, record_id)
