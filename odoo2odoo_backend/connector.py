# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp.addons.connector.connector import ConnectorEnvironment

_logger = logging.getLogger(__name__)


def get_environment(session, model_name, backend_id):
    """Create an environment to work with."""
    backend_record = session.env['odoo.backend'].browse(backend_id)
    return ConnectorEnvironment(backend_record, session, model_name)


def create_bindings(session, model_name, record_id):
    """Create binding records for all backends."""
    for backend in session.env['odoo.backend'].search([]):
        create_binding(session, model_name, record_id, backend.id)


def create_binding(session, model_name, record_id, backend_id, force=False):
    """Create the binding record for a given backend without any external
    Odoo ID. This record will then be exported to the backend.

    This function assumes that the corresponding binding model of `model_name`
    is `odoo.{model_name}` (e.g. `res.partner` => `odoo.res.partner`).
    """
    # FIXME use 'odoo.backend'.get_model_bindings() method and do not assume
    # that binding data model names are prefixed with 'odoo.*'
    if not force and session.env.context.get('connector_no_export'):
        return
    if session.env.context.get('connector_check_recursivity'):
        return
    backend = session.env['odoo.backend'].browse(backend_id)
    binding_model = session.env['odoo.%s' % model_name]
    record = session.env[model_name].browse(record_id)
    binding = binding_model.search(
        [('backend_id', '=', backend.id), ('odoo_id', '=', record_id)])
    if not binding:
        binding_vals = {
            'backend_id': backend.id,
            'odoo_id': record_id,
        }
        # 'create' will trigger a 'write' on the normal data model
        # Try to avoid a recursive call with a context key
        binding = binding_model.with_context(
            connector_check_recursivity=True).create(binding_vals)
        _logger.info(
            u"%s - Binding '%s' created for record '%s'",
            backend.name,
            binding, record)
    else:
        binding.write({})
    return binding
