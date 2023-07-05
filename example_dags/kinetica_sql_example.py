##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

import pendulum
from textwrap import dedent
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models.baseoperator import chain
from airflow.providers.common.sql.operators.sql import SQLTableCheckOperator
from kinetica_provider.operator.sql import KineticaSqlOperator
from kinetica_provider.hooks.sql import KineticaSqlHook


@dag(
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["kinetica"],
    params={ "schema": Param(default="demo", type="string") }
)
def kinetica_sql_example():
    """
    ### Kinetica Example DAG
    This DAG contains 3 tasks for testing SQL connectivity to the Kinetica database and it has a custom param `schema`.

    ### Testing

    You can run the DAG directly from the web UI or you can execute tasks independently:
    
    ```
    $ airflow tasks test kinetica_sql_example kinetica_sql_ddl
    $ airflow tasks test kinetica_sql_example kinetica_sql_multi_line
    $ airflow tasks test kinetica_sql_example kinetica_table_check
    $ airflow tasks test kinetica_sql_example kinetica_sql_hook
    ```
    """

    kinetica_sql_ddl = KineticaSqlOperator(
        doc_md='Demonstrate DDL with templating.',
        task_id="kinetica_sql_ddl",
        sql='''
        create or replace table "{{ params.schema }}"."airflow_test"
        (
            "dt" DATE (dict) NOT NULL,
            "str_val" VARCHAR (32, primary_key) NOT NULL,
            "int_val" integer NOT NULL
        )
        ''',
        split_statements=False,
        return_last=False,
        show_return_value_in_logs=True
    )

    kinetica_sql_multi_line = KineticaSqlOperator(
        doc_md='Demonstrate multi-line SQL',
        task_id="kinetica_sql_multi_line",
        sql='''
            insert into /* ki_hint_update_on_existing_pk */ "{{ params.schema }}"."airflow_test" 
            values( DATE('2023-07-04'), 'val', 1);
            SELECT '{{ ds }}';
        ''',
        split_statements=True,
        return_last=False,
        show_return_value_in_logs=True
    )

    kinetica_table_check = SQLTableCheckOperator(
        doc_md='''
        Verify table contents.
        See [Airflow Docs](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html#check-sql-table-values).
        ''',
        task_id="kinetica_table_check",
        table = '"{{ params.schema }}"."airflow_test"',
        checks = {
            "row_count_check": { "check_statement": "COUNT(*) = 1" }
        },
        partition_clause = None,
        conn_id = "kinetica_default"
    )

    @task
    def kinetica_sql_hook(params={}):
        """
        ### Example Hook

        Use the KineticaHook to create a GPUdb connection and execute a SQL query.
        """
        import logging
        TLOG = logging.getLogger("airflow.task")
        TLOG.info(f"Got params: {params}")

        #for key, value in kwargs.items():
        #    TLOG.info(f"Param {key}: {value}")

        kinetica_hook = KineticaSqlHook()
        status, message = kinetica_hook.test_connection()
        TLOG.info(f"test_connection {status}: {message}")

        sql_result = kinetica_hook.get_first(f'''\
            select * from "{ params['schema'] }"."airflow_test";
        ''')
        TLOG.info(f"get_first: {sql_result}")

        sql_result = kinetica_hook.get_records(f'''\
            select * from "{ params['schema'] }"."airflow_test";
        ''')
        TLOG.info(f"get_records: {sql_result}")


    #kinetica_sql_ddl >> kinetica_sql_multi_line >> kinetica_sql_hook()
    chain(kinetica_sql_ddl, kinetica_sql_multi_line, kinetica_table_check, kinetica_sql_hook())

dag = kinetica_sql_example()
