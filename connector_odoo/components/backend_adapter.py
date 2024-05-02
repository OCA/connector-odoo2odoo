# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    import odoorpc
except ImportError:
    _logger.debug("Cannot import 'odoorpc' Lib")

try:
    import oerplib
except ImportError:
    _logger.debug("Cannot import 'oerplib' Lib")


class OdooLocation(object):
    __slots__ = (
        "hostname",
        "login",
        "password",
        "database",
        "port",
        "version",
        "protocol",
        "lang_id",
        "use_custom_api_path",
    )

    def __init__(
        self,
        hostname,
        login,
        password,
        database,
        port,
        version,
        protocol,
        lang_id="en_US",
        use_custom_api_path=False,
    ):
        self.hostname = hostname
        self.login = login
        self.password = password
        self.database = database
        self.port = port
        self.version = version
        self.protocol = protocol
        self.lang_id = lang_id


class OdooAPI(object):
    def __init__(self, location):
        """
        :param location: Odoo location
        :type location: :class:`OdooLocation`
        """
        self._location = location
        self._api = None

    def _api_login(self, api):
        if self._location.version == "6.1":
            try:
                api.login(
                    database=self._location.database,
                    user=self._location.login,
                    passwd=self._location.password,
                )
            except odoorpc.error.RPCError as e:
                _logger.exception(e)
                raise UserError(e) from e
        else:
            try:
                api.login(
                    db=self._location.database,
                    login=self._location.login,
                    password=self._location.password,
                )
            except odoorpc.error.RPCError as e:
                _logger.exception(e)
                raise UserError(e) from e

    @property
    def api(self):
        if self._api is None:
            if self._location.version == "6.1":
                api = oerplib.OERP(
                    server=self._location.hostname,
                    port=self._location.port,
                    protocol=self._location.protocol,
                )
            else:
                api = odoorpc.ODOO(
                    host=self._location.hostname,
                    port=self._location.port,
                    protocol=self._location.protocol,
                )

            self._api_login(api)
            self._api = api

            _logger.debug("Associated lang %s to location" % self._location.lang_id)
            if self._location.lang_id:
                if self._location.version in ("6.1",):
                    self._api.context["lang"] = self._location.lang_id
                else:
                    self._api.env.context["lang"] = self._location.lang_id

            _logger.info(
                "Created a new Odoo API instance and logged In with context %s"
                % self._api.env.context
                if hasattr(self._api, "env")
                else self._api.context
            )
        return self._api

    def complete_check(self):
        api = self.api
        if not api.version.startswith(self._location.version):
            raise UserError(
                _("Server indicates version %s. Please adapt your conf")
            ) % api.version

        self._api_login(api)

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _logger.debug(traceback)


class OdooCRUDAdapter(AbstractComponent):
    """External Records Adapter for Odoo"""

    _name = "odoo.crud.adapter"
    _inherit = ["base.backend.adapter", "base.odoo.connector"]
    _usage = "backend.adapter"

    def search(self, filters=None):
        """Search records according to some criterias
        and returns a list of ids"""
        raise NotImplementedError

    # pylint: disable=W8106
    def read(self, *kwargs):
        """Returns the information of a record"""
        raise NotImplementedError

    # pylint: disable=W8106
    def search_read(self, *kwargs):
        """Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    # pylint: disable=W8106
    def create(self, *kwargs):
        """Create a record on the external system"""
        raise NotImplementedError

    # pylint: disable=W8106
    def write(self, *kwargs):
        """Update records on the external system"""
        raise NotImplementedError

    # pylint: disable=W8106
    def delete(self, *kwargs):
        """Delete a record on the external system"""
        raise NotImplementedError

    # pylint: disable=W8106
    def execute(self, *kwargs):
        """Execute method for a record on the external system"""
        raise NotImplementedError


class GenericAdapter(AbstractComponent):
    _name = "odoo.adapter"
    _inherit = "odoo.crud.adapter"

    # _odoo_model = None
    # _admin_path = None

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        """Search records according to some criterias
        and returns a list of ids
        :rtype: list
        """

        ext_model = model or self._odoo_model

        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError as e:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            ) from e

        model = (
            odoo_api.env[ext_model]
            if odoo_api.version != "6.1"
            else odoo_api.get(ext_model)
        )
        return model.search(
            filters if filters else [], offset=offset, limit=limit, order=order
        )

    # pylint: disable=W8106,W0622
    def read(self, id, attributes=None, model=None, context=None):
        """Returns the information of a record
        :rtype: dict
        """
        arguments = int(id)
        ext_model = model or self._odoo_model
        if attributes:
            # Avoid to pass Null values in attributes. Workaround for
            # https://bugs.launchpad.net/openerp-connector-Odoo/+bug/1210775
            # When Odoo is installed on PHP 5.4 and the compatibility patch
            # http://odoo.com/blog/Odoo-news/Odoo-now-supports-php-54
            # is not installed, calling info() with None in attributes
            # would return a wrong result (almost empty list of
            # attributes). The right correction is to install the
            # compatibility patch on odoo.
            arguments.append(attributes)

        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError as e:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            ) from e
        model = (
            odoo_api.env[ext_model]
            if odoo_api.version != "6.1"
            else odoo_api.get(ext_model)
        )
        if context:
            return model.with_context(**context).browse(arguments)
        return model.browse(arguments)

    def create(self, data):
        ext_model = self._odoo_model
        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError as e:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            ) from e
        model = (
            odoo_api.env[ext_model]
            if odoo_api.version != "6.1"
            else odoo_api.get(ext_model)
        )
        return model.create(data)

    def write(self, id, data):
        arguments = [int(id)]
        # ext_model = self._odoo_model
        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError as e:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            ) from e
        model = (
            odoo_api.env[self._odoo_model]
            if odoo_api.version != "6.1"
            else odoo_api.get(self._odoo_model)
        )
        object_id = model.browse(arguments)
        # TODO: Check the write implementation of odoorpc
        return object_id.write(data)
