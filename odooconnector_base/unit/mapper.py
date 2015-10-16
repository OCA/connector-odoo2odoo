# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp.addons.connector.unit.mapper import (ExportMapChild,
                                                  ImportMapChild,
                                                  ImportMapper,
                                                  mapping)


_logger = logging.getLogger(__name__)


class OdooImportMapper(ImportMapper):
    """ Base Import Mapper for Odoo2Odoo """
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class OdooExportMapChild(ExportMapChild):

    def format_items(self, item_values):
        items = super(OdooExportMapChild, self).format_items(
            item_values
        )
        # The (0, 0, data) creates a new line, linked to the parent order
        # For an betterexplanation what the tripple (0,0 data) and (5,0) means,
        # see 'Odoo Development Essentials' p.64: 'Setting values for
        # relational fields'
        return [(5, 0)] + [(0, 0, data) for data in items]


class OdooImportMapChild(ImportMapChild):

    def format_items(self, item_values):
        items = super(OdooImportMapChild, self).format_items(
            item_values
        )
        return [(5, 0)] + items
