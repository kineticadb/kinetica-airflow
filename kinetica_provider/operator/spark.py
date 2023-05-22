##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

from __future__ import annotations
from typing import Any, Sequence
from os import path
from configparser import ConfigParser, ExtendedInterpolation
from urllib.parse import urlparse, ParseResult

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.providers.apache.spark.hooks.spark_submit import SparkSubmitHook
from airflow.utils.context import Context, ConnectionAccessor
from airflow.models.dag import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.models.connection import Connection
from airflow.models import BaseOperator, BaseOperatorLink
from enum import Enum
from airflow.models.taskinstance import TaskInstanceKey
from airflow.models.xcom import XCom

class KineticaSparkLink(BaseOperatorLink):
    """
    Custom URL link for Airflow task UI

    see https://airflow.apache.org/docs/apache-airflow/stable/howto/define_extra_link.html
    """

    name = "Spark Log"

    # This is an alternative to operator_extra_links
    #operators = [ KineticaSparkOperator ]

    def get_link(self, operator: BaseOperator, *, ti_key: TaskInstanceKey):
        return XCom.get_value(ti_key=ti_key, key="log_url")

class LoaderMode(Enum):
    REFRESH = 1
    APPEND = 2

class KineticaSparkOperator(BaseOperator):
    """
    ### Kineitca Spark submit operator

    This operator executes a `SparkSubmitHook` that will run the Kinetica import job `com.kinetica.fsq.TransformPlaces`.

    Required parameters:

    :param dest_table: Destination kinetica schama.table
    :param source_path: Source parquet path.
    :param mode: You must specify "refresh" or "append" mode.

    Optional parameters:

    :param base_path: Base path of parquet file if source_path contains partitions (default: None)
    :param row_limit: Maximum number of rows to ingest. (default: None)
    :param conf_file: Location of configuration file. (default: in DAG directory)
    :param parallelism: Paralell threads used for ingest (default: 4)
    :param application: Application jar or py file. (default: from conf file)
    :param conn_id: Spark connection ID (default: spark_default)
    :param name: Application name (default: task_instance_key_str)
    :param verbose: Use verbose logging (default: False)
    :param test_skip_submit: Skip the driver execution on Spark (testing only)
    :param h3_from: Crate H3 shard key from columns
    """

    SPARK_URL_TEMPLATE = "http://{hostname}:8082/logPage/?driverId={driver_id}&logType=stderr"

    template_fields: Sequence[str] = (
        "_conf_file",
        "_source_path",
        "_base_path",
        "_application",
        "_name",
        "_dest_table",
        "_date_filter",

        # "_application",
        # "_conf",
        # "_files",
        # "_py_files",
        # "_jars",
        # "_driver_class_path",
        # "_packages",
        # "_exclude_packages",
        # "_keytab",
        # "_principal",
        # "_proxy_user",
        # "_name",
        # "_application_args",ß
        # "_env_vars",
    )

    ui_color = "#562da2"
    ui_fgcolor = "#FFFFFF"

    operator_extra_links = ( KineticaSparkLink(), )

    def __init__(
        self,
        *,
        dest_table: str,
        source_path: str,
        mode: LoaderMode,
        date_filter: str | None = None,
        base_path: str | None = None,
        row_limit: int | None = None,
        conf_file: str | None = None,
        parallelism: int | None = 4,
        test_skip_submit: bool | None = False,
        h3_from: str | None = None,

        application: str | None = None,
        # conf: dict[str, Any] | None = None,
        conn_id: str = "spark_default",
        # files: str | None = None,
        # py_files: str | None = None,
        # archives: str | None = None,
        # driver_class_path: str | None = None,
        # jars: str | None = None,
        # java_class: str | None = None,
        # packages: str | None = None,
        # exclude_packages: str | None = None,
        # repositories: str | None = None,
        # total_executor_cores: int | None = None,
        # executor_cores: int | None = None,
        # executor_memory: str | None = None,
        # driver_memory: str | None = None,
        # keytab: str | None = None,
        # principal: str | None = None,
        # proxy_user: str | None = None,
        name: str | None = None,
        # num_executors: int | None = None,
        # status_poll_interval: int = 1,
        # application_args: list[Any] | None = None,
        # env_vars: dict[str, Any] | None = None,
        verbose: bool = False,
        # spark_binary: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._dest_table = dest_table
        self._source_path = source_path
        self._mode = mode
        self._base_path = base_path
        self._date_filter = date_filter
        self._row_limit = row_limit
        self._conf_file = conf_file
        self._parallelism = parallelism
        self._test_skip_submit = test_skip_submit
        self._h3_from = h3_from

        self._application = application
        # self._conf = conf
        self._conn_id = conn_id
        # self._files = files
        # self._py_files = py_files
        # self._archives = archives
        # self._driver_class_path = driver_class_path
        # self._jars = jars
        # self._java_class = java_class
        # self._packages = packages
        # self._exclude_packages = exclude_packages
        # self._repositories = repositories
        # self._total_executor_cores = total_executor_cores
        # self._executor_cores = executor_cores
        # self._executor_memory = executor_memory
        # self._driver_memory = driver_memory
        # self._keytab = keytab
        # self._principal = principal
        # self._proxy_user = proxy_user
        self._name = name
        # self._num_executors = num_executors
        # self._status_poll_interval = status_poll_interval
        # self._application_args = application_args
        # self._env_vars = env_vars
        self._verbose = verbose
        #self._spark_binary = spark_binary
        self._hook: SparkSubmitHook | None = None


    def execute(self, context: Context) -> None:
        """Call the SparkSubmitHook to run the provided spark job"""

        if self._dest_table is None:
            raise ValueError("dest_table is required")
        
        if self._source_path is None:
            raise ValueError("source_path is required")

        if(self._name is None):
            self._name = context['task_instance_key_str']
        
        self.log.info(f"Application name: {self._name}")

        # read the config file
        if(self._conf_file is None):
            dag: DAG = context['dag']
            self._conf_file = path.join(dag.folder, 'kinetica_spark.conf')

        self.log.info(f"Reading config file: {self._conf_file}")
        self._parse_conf(self._conf_file)

        # create and submit the hook
        self._hook = SparkSubmitHook(
            java_class="com.kinetica.fsq.KineticaLoader",
            name=self._name,
            conn_id=self._conn_id,
            verbose=self._verbose,
            conf=self._spark_conf
        )

        if(not self._test_skip_submit):
            self._hook.submit(application=self._application)
            driver_id = self._hook._driver_id
        else:
            for key,val in self._spark_conf.items():
                self.log.info(f"PARAM: <{key}> = <{val}>")
            driver_id = 'test_skip_submit'

        self.log.info(f"Completed excution of driver: {driver_id}")

        # return responses in xcom
        log_url = self._build_log_url(context, driver_id)

        spark_submit_cmd = self._hook._build_spark_submit_command(self._application)

        task_instance: TaskInstance = context['task_instance']
        task_instance.xcom_push('log_url', log_url)
        task_instance.xcom_push('driver_id', driver_id)
        task_instance.xcom_push('driver_status', self._hook._driver_status)
        task_instance.xcom_push('application_name', self._name)
        task_instance.xcom_push('command', self._hook._mask_cmd(spark_submit_cmd))


    def on_kill(self) -> None:
        if self._hook is None:
            raise AirflowException("Can't kill task not yet submitted.") 
        self._hook.on_kill()


    def _parse_conf(self, config_file: str) -> None:
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.read_file(open(config_file))

        self._spark_conf = config['spark']
        kinetica_conf = config['kinetica']

        # input params
        self._spark_conf['spark.4sq.transform.dest-table'] = self._dest_table
        self._spark_conf['spark.4sq.transform.source-path'] = self._source_path
        self._spark_conf['spark.4sq.transform.row-limit'] = str(self._row_limit)
        self._spark_conf['spark.4sq.transform.mode'] = self._mode.name

        if(self._base_path):
            self._spark_conf['spark.4sq.transform.base-path'] = self._base_path

        if(self._date_filter):
            self._spark_conf['spark.4sq.transform.date-filter'] = self._date_filter
        
        if(self._h3_from):
            self._spark_conf["spark.4sq.transform.h3-from"] = self._h3_from

        # REST mode must be enabled for the SparkSubmitHook to work
        self._spark_conf["spark.master.rest.enabled"] = "true"

        # We need to control paralellism or we could get errors
        self._spark_conf["spark.default.parallelism"] = str(self._parallelism)

        if(self._application is None):
            self._application = kinetica_conf['application-jar']
        self.log.info(f"Application file: {self._application}")


    def _build_log_url(self, context: Context, driver_id: str) -> str:
        # get the connection
        conn: ConnectionAccessor = context['conn']
        spark_conn: Connection = conn.get(self._conn_id)

        # extract hostname
        master_url = spark_conn.host
        url_parse: ParseResult = urlparse(master_url)
        hostname = url_parse.hostname

        # this may need to be a template
        log_url = self.SPARK_URL_TEMPLATE.format(
            hostname=hostname, driver_id=driver_id)

        return log_url

