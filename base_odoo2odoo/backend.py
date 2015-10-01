# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import openerp.addons.connector.backend as backend


ic_odoo = backend.Backend('odoo')
ic_odoo900 = backend.Backend(parent=ic_odoo, version='900')
ic_odoo800 = backend.Backend(parent=ic_odoo, version='800')
ic_odoo700 = backend.Backend(parent=ic_odoo, version='700')
