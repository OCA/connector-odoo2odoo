# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class ProductAttributeImporter(Component):
    """ Import Odoo UOM """

    _name = "odoo.product.attribute.importer"
    _inherit = "odoo.importer"
    _apply_on = "odoo.product.attribute"


class ProductAttributeMapper(Component):
    _name = "odoo.product.attribute.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.product.attribute"

    direct = [("name", "name"), ("create_variant", "create_variant")]

    @only_create
    @mapping
    def check_att_exists(self, record):
        # TODO: Improve and check family, factor etc...
        att_id = self.env["product.attribute"].search(
            [
                ("name", "=", record.name),
                ("create_variant", "=", record["create_variant"]),
            ]
        )
        res = {}
        if len(att_id) == 1:
            res.update({"odoo_id": att_id.id})

        return res

    @mapping
    def create_variant(self, record):
        res = {"create_variant": "no_variant"}
        if record.create_variant:
            res.update(create_variant="always")
        return res
