# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class OdooImportMapper(AbstractComponent):
    _name = 'odoo.import.mapper'
    _inherit = ['base.odoo.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class MagentoExportMapper(AbstractComponent):
    _name = 'odoo.export.mapper'
    _inherit = ['base.odoo.connector', 'base.export.mapper']
    _usage = 'export.mapper'


