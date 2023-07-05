##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

from __future__ import annotations

from typing import Any, Sequence
from textwrap import dedent
from sqlalchemy import Boolean, Column, Integer, String, Text

from airflow.models.connection import Connection
from airflow.providers.common.sql.hooks.sql import DbApiHook
from airflow.utils.log.logging_mixin import LoggingMixin
import logging
from airflow.utils.strings import to_boolean

from gpudb import ( GPUdb, GPUdbException, GPUdbRecord )

class KineticaConnection(GPUdb):
    """
    Proxy for GPUdb connection class to provide support for [PEP-0249](https://peps.python.org/pep-0249/) compliant connection.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def commit(self) -> None:
        # do nothing
        pass

    def close(self) -> None:
        # do nothing
        pass

    def cursor(self) -> Any:
        return KineticaCursor(self)


class KineticaCursor(LoggingMixin):
    """
    Cursor class to provide support for [PEP-0249](https://peps.python.org/pep-0249/) compliant connection.
    """

    @staticmethod
    def execute_sql(kdbc: KineticaConnection, sql_statement: str) -> Any:
        response = kdbc.execute_sql_and_decode(sql_statement, get_column_major=False)
        if(response.status_info['status'] != 'OK'):
            raise ValueError(f"SQL statement failed: {response.status_info['message']}")
        kdbc.log.info(f"SQL completed (rows={response.total_number_of_records}, time={response.status_info['response_time']})")
        kdbc.log.info(f"SQL response {response})")
        return response
    

    def __init__(self, kdbc: KineticaConnection, *args, **kwargs) -> None:
        self.kdbc: KineticaConnection = kdbc
        self.rowcount: int = -1
        self.description: Sequence[Column] = None
        self._records = None
        super().__init__(*args, **kwargs)


    def close(self) -> None:
        # do nothing
        pass


    def execute(self, sql_statement: str) -> list:
        response = KineticaCursor.execute_sql(self.kdbc, sql_statement)
        self.rowcount = response.total_number_of_records

        #self.description = [ Column('result', Integer) ]
        # this is a hack but fortunately most operators don't check the types.
        self.description = True

        self._records = response.records

    
    def fetchall(self) -> list[tuple] | None:
        #raise NotImplementedError()
        if(self.rowcount < 0):
            return None
        return [ list(rec.values()) for rec in self._records]


    def fetchone(self) -> tuple | None:
        if(self.rowcount != 1):
            raise ValueError(f"Query should return one record. Got: {self.rowcount}")
        return self.fetchall()[0]

def _try_to_boolean(value: Any):
    if isinstance(value, (str, type(None))):
        return to_boolean(value)
    return value


class KineticaSqlHook(DbApiHook):
    """
    Hook for Kinetica SQL access.
    """

    @staticmethod
    def get_connection_form_widgets() -> dict[str, Any]:
        """Returns connection widgets to add to connection form"""
        from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
        from flask_babel import lazy_gettext
        from wtforms import BooleanField, StringField

        return {
            "timeout": StringField(lazy_gettext("Timeout"), widget=BS3TextFieldWidget(), description="Connection timeout in milliseconds"),
            "disable_auto_discovery": BooleanField(label=lazy_gettext("Disable Auto Discovery"), description="Don't get other connection URL's"),
            "disable_failover": BooleanField(label=lazy_gettext("Disable Failover"), description="Don't failover if HA is enabled."),
            "enable_driver_log": BooleanField(label=lazy_gettext("Enable Driver Log"), description="More detailed logging from the driver."),
        }

    @staticmethod
    def get_ui_field_behaviour() -> dict:
        """Returns custom field behaviour"""
        import json

        return {
            "hidden_fields": ["schema", "extra", "port" ],
            "relabeling": { "host" : "Kinetica URL" },
            "placeholders": { },
            "disable_auto_discovery" : "Disable Auto Discovery",
            "disable_failover" : "Disable Failover",
            "timeout" : "Connection Timeout",
            "enable_driver_log" : "Enable Driver Log"
        }

    @staticmethod
    def execute_sql(kdbc: KineticaConnection, sql_statement: str) -> None:
        sql_statement_d = dedent(sql_statement)
        kdbc.log.info(f"Executing SQL... {sql_statement_d}")
        return KineticaCursor.execute_sql(kdbc, sql_statement)

    conn_name_attr = "kinetica_conn_id"
    default_conn_name = "kinetica_default"
    conn_type = "kinetica"
    hook_name = "Kinetica"
    supports_autocommit = False

    def __init__(self, *args, **kwargs) -> None:
        args_str = ','.join(map(str,args))
        kwargs_str = ','.join('{}={}'.format(k,v) for k,v in kwargs.items())
        self.log.info("Init KineticaHook: (%s)", ','.join([args_str,kwargs_str]))
        super().__init__(*args, **kwargs)


    def get_conn(self) -> KineticaConnection:
        conn: Connection = self.get_connection(getattr(self, self.conn_name_attr))
        
        extra_dict = conn.extra_dejson
        self.log.info("Extra JSON: %s", extra_dict)

        opts = GPUdb.Options.default()

        dict_val = extra_dict.get("disable_auto_discovery")
        if dict_val is not None:
            opts.disable_auto_discovery = _try_to_boolean(dict_val)

        dict_val = extra_dict.get("disable_failover")
        if dict_val is not None:
            opts.disable_failover = _try_to_boolean(dict_val)

        dict_val = extra_dict.get("timeout")
        if dict_val is not None:
            opts.timeout = dict_val

        dict_val = extra_dict.get("enable_driver_log")
        if dict_val is not None:
            opts.logging_level = "info"

        opts.username = conn.login
        opts.password = conn.password

        #opts.logging_level = logging.DEBUG
        self.log.info("Connection options: %s", opts)
        kinetica_dbc = KineticaConnection(host = conn.host, options = opts)

        try:
            self.log.info("Connecting to URL: (%s)", kinetica_dbc.get_url())
            response = kinetica_dbc.show_system_properties(options = { 'properties': 'version.gpudb_core_version'})
            server_version = response.property_map['version.gpudb_core_version']
            self.log.info("Connected to Kinetica (version %s)", server_version)
        except GPUdbException as ex:
            raise ValueError(f"{ex.__class__.__name__}: {ex.message}")

        return kinetica_dbc
