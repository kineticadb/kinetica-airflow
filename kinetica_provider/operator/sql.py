##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

from typing import Sequence
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from kinetica_provider.hooks.sql import KineticaSqlHook

class KineticaSqlOperator(SQLExecuteQueryOperator):
    """
    Executes SQL code in a Kinetica database.
    """

    template_fields: Sequence[str] = ("sql","parameters")
    template_ext: Sequence[str] = (".sql",)
    template_fields_renderers = {"sql": "sql", "parameters": "json"}
    
    ui_color = "#562da2"
    ui_fgcolor = "#FFFFFF"

    def __init__(self, *, kinetica_conn_id: str = "kinetica_default", **kwargs) -> None:
        super().__init__(conn_id=kinetica_conn_id, **kwargs)

    def get_db_hook(self) -> KineticaSqlHook:
        return KineticaSqlHook(kinetica_conn_id=self.conn_id)
