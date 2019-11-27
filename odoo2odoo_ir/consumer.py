# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import OrderedDict
import sys

from openerp.addons.connector.event import on_record_create, on_record_write

from openerp.addons.odoo2odoo_backend.connector import create_bindings
from openerp.addons.odoo2odoo_backend.unit.binder import OdooModelBinder
from openerp.addons.odoo2odoo_backend.unit.backend_adapter \
    import GenericCRUDAdapter
from openerp.addons.odoo2odoo_backend.unit.mapper import (
    OdooImportMapper, OdooExportMapper)
from openerp.addons.odoo2odoo_backend.unit.import_synchronizer import (
    OdooImporter, DirectBatchOdooImporter, DelayedBatchOdooImporter)
from openerp.addons.odoo2odoo_backend.unit.export_synchronizer import (
    OdooExporter, export_binding)
from openerp.addons.odoo2odoo_backend.backend import odoo


# Data models to synchronize (with their binding model)
BINDINGS = OrderedDict([
    ('ir.translation', 'odoo.ir.translation'),
])


@on_record_create(model_names=BINDINGS.keys())
@on_record_write(model_names=BINDINGS.keys())
def on_event_create_bindings(session, model_name, record_id, vals):
    create_bindings(session, model_name, record_id)


@on_record_create(model_names=BINDINGS.values())
@on_record_write(model_names=BINDINGS.values())
def delay_export_binding(session, model_name, record_id, vals):
    if session.env.context.get('connector_no_export'):
        return
    export_binding.delay(
        session, model_name, record_id,
        priority=2147483647)    # Lower priority (max PostgreSQL integer value)


@odoo
class OdooSyncBinder(OdooModelBinder):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncAdapter(GenericCRUDAdapter):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncImportMapper(OdooImportMapper):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncExportMapper(OdooExportMapper):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncImporter(OdooImporter):
    _model_name = BINDINGS.values()
    _raw_mode = True


@odoo
class OdooSyncDirectBatchImporter(DirectBatchOdooImporter):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncDelayedBatchImporter(DelayedBatchOdooImporter):
    _model_name = BINDINGS.values()


@odoo
class OdooSyncExporter(OdooExporter):
    _model_name = BINDINGS.values()
