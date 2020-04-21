# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class OdooModelBinder(Component):
    """ Bind records and give odoo/odoo ids correspondence

    Binding models are models called ``odoo.{normal_model}``,
    like ``odoo.res.partner`` or ``odoo.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Odoo ID, the ID of the Odoo Backend and the additional
    fields belonging to the Odoo instance.
    """

    _name = "odoo.binder"
    _inherit = ["base.binder", "base.odoo.connector"]
    _apply_on = [
        "odoo.uom.uom",
        "odoo.product.attribute",
        "odoo.product.attribute.value",
        "odoo.product.category",
        "odoo.product.product",
        "odoo.product.template",
        "odoo.product.pricelist",
        "odoo.res.partner",
        # TODO:
        # 'odoo.res.partner.category',
        # 'odoo.stock.picking',
        # 'odoo.sale.order',
        # 'odoo.sale.order.line',
        # 'odoo.account.invoice',
    ]

    def wrap_binding(self, regular, browse=False):
        """ For a normal record, gives the binding record.

        Example: when called with a ``product.product`` id,
        it will return the corresponding ``odoo.product.product`` id.
        it assumes that bind_ids is the name used for bind regular to
        external objects
        :param browse: when True, returns a browse_record instance
                       rather than an ID
        """
        try:
            bindings = regular.bind_ids
        except Exception:
            raise ValueError(
                "Cannot wrap model %s, because it has no %s fields"
                % (self.model._name, "bind_ids")
            )
        bind = bindings.filtered(
            lambda b: b.backend_id.id == self.backend_record.id
        )
        bind.ensure_one()
        return bind[self._external_field]
