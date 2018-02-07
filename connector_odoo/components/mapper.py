# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping

class OdooImportMapper(AbstractComponent):
    _name = 'odoo.import.mapper'
    _inherit = ['base.odoo.connector', 'base.import.mapper']
    _usage = 'import.mapper'
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class OdooExportMapper(AbstractComponent):
    _name = 'odoo.export.mapper'
    _inherit = ['base.odoo.connector', 'base.export.mapper']
    _usage = 'export.mapper'


