# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.connector import Binder

from ..backend import odoo


class OdooBinder(Binder):
    """Generic Binder for a Odoo backend."""


@odoo
class OdooModelBinder(OdooBinder):
    """
    Bindings are done directly on the binding model.

    Binding models are models called ``odoo.{normal_model}``,
    like ``odoo.res.partner`` or ``odoo.product.product``.
    They are ``_inherits`` of the normal models and contains
    the external Odoo ID, the ID of the Odoo backend and the additional
    fields belonging to the Odoo instance.
    """
    _model_name = []
    _external_field = 'external_odoo_id'
    _backend_field = 'backend_id'
    _openerp_field = 'odoo_id'
    _sync_date_field = 'sync_date'
