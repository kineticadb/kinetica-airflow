# Kinetica Provider for Apache Airflow

The `airflow-provider-kinetica` package provides a SQL operator and hook for Kinetica.

- [1. Overview](#1-overview)
- [1.2. Installation](#12-installation)
- [2. Testing](#2-testing)
    - [2.1. Configure Conda environment](#21-configure-conda-environment)
    - [2.2. Install Airflow](#22-install-airflow)
    - [2.3. Start Airflow in Standalone mode](#23-start-airflow-in-standalone-mode)
    - [2.4. Install the package in editable mode.](#24-install-the-package-in-editable-mode)
- [3. Building](#3-building)
- [4. See Also](#4-see-also)

## 1. Overview

Features included in this package are:

* Airflow hook KineticaSqlHook
* Airflow operator KineticaSqlOperator
* Custom connection type with customized connection UI.

Relevant files are:

| File                                                                             | Description                         |
| -------------------------------------------------------------------------------- | ----------------------------------- |
| [kinetica_provider/get_provider_info.py](kinetica_provider/get_provider_info.py) | Provider info                       |
| [example_dags/kinetica_sql_example.py](example_dags/kinetica_sql_example.py)     | Example DAG with operator and hook. |
| [kinetica_provider/operator/sql.py](kinetica_provider/operator/sql.py)           | Contains KineticaSqlHook            |
| [kinetica_provider/hooks/sql.py](kinetica_provider/operator/sql.py)              | Contains KineticaSqlOperator        |

## 1.2. Installation

This step assumes that you have an existing distribution of the package. If not then you will need to follow the steps in [3. Building](#3-building).

The package can be installed from the `whl` file.

```sh
$ pip install ./dist/airflow_provider_kinetica-1.0.0-py3-none-any.whl
[...]
Successfully installed airflow-provider-kinetica-1.0.0
```

You will need to create a default connection named `kinetica_default`. You can do this in the web UI or with the following syntax:

```bash
$ airflow connections add 'kinetica_default' \
    --conn-type 'kinetica' \
    --conn-login 'admin' \
    --conn-password '???'  \
    --conn-host 'http://g-p100-300-301-u29.tysons.kinetica.com:9191/'
```

## 2. Testing 

This section explains how to setup an environment used for build and test.

### 2.1. Configure Conda environment

To run Airflow we need a specific version of python with its dependencies and so we will use miniconda. 

The following steps show how to install miniconda on Linux. You should check the [Miniconda documentation][MINICONDA] for the most recent install instructions.

[MINICONDA]: <https://docs.conda.io/en/latest/miniconda.html> "Miniconda Installation"

```sh
[~]$ wget https://repo.anaconda.com/miniconda/Miniconda3-py38_23.3.1-0-Linux-x86_64.sh
[~]$ bash Miniconda3-py38_23.3.1-0-Linux-x86_64.sh
```

After installing make sure you are in the `base` conda environment. Next we crate an `airflow` conda environment. 

```sh
(base) [~]$ conda create --name airflow python=3.8
(base) [~]$ conda activate airflow
(airflow) [~]$ 
```

### 2.2. Install Airflow

These steps will show how to configure a [standalone Airflow environment][STANDALONE]. 

[STANDALONE]: <https://airflow.apache.org/docs/apache-airflow/stable/start.html> "Airflow Quick Start"

*Note: Before starting make sure you have activated the `airflow` conda envionmnet.*

Determine the download URL of the airflow installer.

```sh
(airflow) [~]$ AIRFLOW_VERSION=2.6.1
(airflow) [~]$ PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
(airflow) [~]$ CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
(airflow) [~]$ echo $CONSTRAINT_URL
https://raw.githubusercontent.com/apache/airflow/constraints-2.6.1/constraints-3.8.txt
```

Install the Airflow package.

```sh
(airflow) [~]$ pip install --upgrade pip
(airflow) [~]$ pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

### 2.3. Start Airflow in Standalone mode

You must provide a location that will be used for the `$AIRFLOW_HOME`. We set this in the conda environment.

```sh
(airflow) [~]$ conda env config vars set AIRFLOW_HOME=~/fsq-airflow/airflow/standalone
(airflow) [~]$ conda env config vars list -n airflow
AIRFLOW_HOME = ~/fsq-airflow/airflow/standalone
```

You must re-activate the environment for the variable to get loaded.

```sh
(airflow) [~]$ conda activate airflow
(airflow) [~]$ echo $AIRFLOW_HOME
~/fsq-airflow/airflow/standalone
```

When you startup airflow in standalone mode it will copy files into `$AIRFLOW_HOME` if they do not already exist. When startup is complete it will show the admin and user password for the webserver.

```sh
(airflow) [~]$ cd $AIRFLOW_HOME
(airflow) [standalone]$ airflow standalone
[...]
standalone | Airflow is ready
standalone | Login with username: admin  password: 39FrRzqzRYTK3pc9
standalone | Airflow Standalone is for development purposes only. Do not use this in production!
```

You can edit the `airflow.cfg` file if you need to change any ports.

### 2.4. Install the package in editable mode.

When a package is installed for edit the contents of the specified directory get registered with the python environment. This allows for changes to be made without the need for reinstalling.

Change to the location of the package and install it as editable.

```sh
(airflow) [~]$ cd ~/fsq-airflow/airflow/airflow-provider-kinetica
(airflow) [airflow-provider-kinetica]$ pip install --editable .
```

Now you can restart airflow to see the installed provider. Uninstall the package when you are done.

```sh
(airflow) [airflow-provider-kinetica]$ python setup.py develop --uninstall
```

## 3. Building

The conda environment created for testing can also be used for building. You will need the buil package.

```sh
(airflow) [~]$ pip install build
```

From the location of the provider execute the build process.

```sh
(airflow) [~]$ cd ~/fsq-airflow/airflow/airflow-provider-kinetica
(airflow) [airflow-provider-kinetica]$ python -m build
[...]
Successfully built airflow-provider-kinetica-1.0.0.tar.gz and airflow_provider_kinetica-1.0.0-py3-none-any.whl
```

It will create a "wheel" distribution package and you can use this to install the provider.

```sh
(airflow) [airflow-provider-kinetica]$ ls -1 ./dist
airflow_provider_kinetica-1.0.0-py3-none-any.whl
airflow-provider-kinetica-1.0.0.tar.gz
(airflow) [airflow-provider-kinetica]$ pip install ./dist/airflow_provider_kinetica-1.0.0-py3-none-any.whl
```

## 4. See Also

* [Kinetica Python API](https://docs.kinetica.com/7.1/api/python/)
* [Managing Connections](https://airflow.incubator.apache.org/docs/apache-airflow/stable/howto/connection.html)
* [SQL Operators](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html)
* [Kinetica SQL](https://docs.kinetica.com/7.1/sql/)
* [Airflow Provider Sample](https://github.com/astronomer/airflow-provider-sample)
