##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

import pendulum
from textwrap import dedent
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models.baseoperator import chain
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
    $ airflow tasks test kinetica_sql_example kinetica_sql_hook
    ```
    """

    kinetica_sql_ddl = KineticaSqlOperator(
        doc_md='Demonstrate DDL with templating.',
        task_id="kinetica_sql_ddl",
        sql='''
            CREATE OR REPLACE TABLE "{{ params.schema }}"."nyctaxi"
            (
                "vendor_id" VARCHAR (4) NOT NULL,
                "pickup_datetime" TIMESTAMP NOT NULL,
                "dropoff_datetime" TIMESTAMP NOT NULL,
                "passenger_count" TINYINT NOT NULL,
                "trip_distance" REAL NOT NULL,
                "pickup_longitude" REAL NOT NULL,
                "pickup_latitude" REAL NOT NULL,
                "rate_code_id" SMALLINT NOT NULL,
                "store_and_fwd_flag" VARCHAR (1) NOT NULL,
                "dropoff_longitude" REAL NOT NULL,
                "dropoff_latitude" REAL NOT NULL,
                "payment_type" VARCHAR (16) NOT NULL,
                "fare_amount" REAL NOT NULL,
                "surcharge" REAL NOT NULL,
                "mta_tax" REAL NOT NULL,
                "tip_amount" REAL NOT NULL,
                "tolls_amount" REAL NOT NULL,
                "total_amount" REAL NOT NULL,
                "cab_type" TINYINT NOT NULL
            )
            TIER STRATEGY (
            ( ( VRAM 1, RAM 5, PERSIST 5 ) )
            );
        ''',
        split_statements=True,
        return_last=False
    )

    kinetica_sql_multi_line = KineticaSqlOperator(
        doc_md='Demonstrate multi-line SQL',
        task_id="kinetica_sql_multi_line",
        sql='''
            SELECT 1; 
            SELECT '{{ ds }}';
        ''',
        split_statements=True,
        return_last=False
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
        kdbc = kinetica_hook.get_conn()

        KineticaSqlHook.execute_sql(kdbc, f'''\
            CREATE OR REPLACE TABLE "{ params['schema'] }"."nyctaxi"
            (
                "vendor_id" VARCHAR (4) NOT NULL,
                "pickup_datetime" TIMESTAMP NOT NULL,
                "dropoff_datetime" TIMESTAMP NOT NULL,
                "passenger_count" TINYINT NOT NULL,
                "trip_distance" REAL NOT NULL,
                "pickup_longitude" REAL NOT NULL,
                "pickup_latitude" REAL NOT NULL,
                "rate_code_id" SMALLINT NOT NULL,
                "store_and_fwd_flag" VARCHAR (1) NOT NULL,
                "dropoff_longitude" REAL NOT NULL,
                "dropoff_latitude" REAL NOT NULL,
                "payment_type" VARCHAR (16) NOT NULL,
                "fare_amount" REAL NOT NULL,
                "surcharge" REAL NOT NULL,
                "mta_tax" REAL NOT NULL,
                "tip_amount" REAL NOT NULL,
                "tolls_amount" REAL NOT NULL,
                "total_amount" REAL NOT NULL,
                "cab_type" TINYINT NOT NULL
            )
            TIER STRATEGY (
            ( ( VRAM 1, RAM 5, PERSIST 5 ) )
            );
        ''')

    #kinetica_sql_ddl >> kinetica_sql_multi_line >> kinetica_sql_hook()
    chain(kinetica_sql_ddl, kinetica_sql_multi_line, kinetica_sql_hook())

dag = kinetica_sql_example()
