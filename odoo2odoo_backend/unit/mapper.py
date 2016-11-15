# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)


class OdooExportMapper(ExportMapper):
    _model_name = None

    @mapping
    def odoo2odoo(self, record):
        """Transform a Odoo's record to its external Odoo's counterpart.
        This method has to return a dictionary of values as expected
        by the external Odoo.
        """
        raise NotImplementedError
