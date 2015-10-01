# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import openerp.addons.connector.backend as backend


oc_odoo = backend.Backend('odoo')
oc_odoo900 = backend.Backend(parent=oc_odoo, version='900')
oc_odoo800 = backend.Backend(parent=oc_odoo, version='800')
oc_odoo700 = backend.Backend(parent=oc_odoo, version='700')
