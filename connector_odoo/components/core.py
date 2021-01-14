# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import AbstractComponent


class BaseOdooConnectorComponent(AbstractComponent):
    """ Base Odoo Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.odoo.connector'
    _inherit = 'base.connector'
    _collection = 'odoo.backend'
