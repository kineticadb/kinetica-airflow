# Kinetica Provider for Apache Airflow

[![PyPI - Version](https://img.shields.io/pypi/v/airflow-provider-kinetica?style=flat&color=orange)](https://pypi.org/project/airflow-provider-kinetica/)
[![GitHub Release](https://img.shields.io/github/v/release/kineticadb/kinetica-airflow?style=flat&logo=github&label=Github%20Release&color=orange)](https://github.com/kineticadb/kinetica-airflow/releases/)
[![Build Distribution](https://github.com/kineticadb/kinetica-airflow/actions/workflows/build.yml/badge.svg)](https://github.com/kineticadb/kinetica-airflow/actions/workflows/build.yml)

The `airflow-provider-kinetica` package provides a SQL operator and hook for Kinetica.

- [1. Overview](#1-overview)
- [2. Installation](#2-installation)
  - [2.1 Optional: Manual Install](#21-optional-manual-install)
- [3. Testing](#3-testing)
  - [3.1. Configure Conda environment](#31-configure-conda-environment)
  - [3.2. Install Airflow](#32-install-airflow)
  - [3.4. Install the package in editable mode](#34-install-the-package-in-editable-mode)
  - [3.3. Start Airflow in Standalone mode](#33-start-airflow-in-standalone-mode)
  - [3.5. Example DAGs](#35-example-dags)
- [5. See Also](#5-see-also)
  - [5.1 Kinetica Docs](#51-kinetica-docs)
  - [5.2 Airflow Docs](#52-airflow-docs)
  - [5.3 Building a Provider](#53-building-a-provider)

## 1. Overview

Features included in this package are:

- Airflow hook `KineticaSqlHook`
- Airflow operator `KineticaSqlOperator`
- Custom connection type with customized connection UI.

Relevant files are:

| File                                                                             | Description                         |
| -------------------------------------------------------------------------------- | ----------------------------------- |
| [kinetica_provider/get_provider_info.py](kinetica_provider/get_provider_info.py) | Provider info                       |
| [example_dags/kinetica_sql_example.py](example_dags/kinetica_sql_example.py)     | Example DAG with operator and hook. |
| [kinetica_provider/operator/sql.py](kinetica_provider/operator/sql.py)           | Contains KineticaSqlHook            |
| [kinetica_provider/hooks/sql.py](kinetica_provider/hooks/sql.py)                 | Contains KineticaSqlOperator        |

## 2. Installation

> Note: Before proceeding make sure airflow is installed according to the [offical installation docs](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html).

This `airflow-provider-kinetica` is available on PyPi. You can install with:

```sh
$ pip install airflow-provider-kinetica
Successfully installed airflow-provider-kinetica-1.0.0
```

You will need to create a default connection named `kinetica_default`. You can do this in the web UI or with the following syntax:

```bash
$ airflow connections add 'kinetica_default' \
    --conn-type 'kinetica' \
    --conn-login 'admin' \
    --conn-password '???'  \
    --conn-host 'http://hostname:9191/'
```

> Note: You will need to restart Airflow complete the installation.

### 2.1 Optional: Manual Install

As an alternative you can  download the `.whl` from the assets section of the [Github release](https://github.com/kineticadb/kinetica-airflow/releases/) for a manual install:

```sh
$ pip install ./airflow_provider_kinetica-1.0.0-py3-none-any.whl
[...]
Successfully installed airflow-provider-kinetica-1.0.0
```

## 3. Testing

This section explains how to setup an environment used for build and test.

### 3.1. Configure Conda environment

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

### 3.2. Install Airflow

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

### 3.4. Install the package in editable mode

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

You will need to create the default Kinetica connection. You can modify this in the **Admin->Connections** dialog.

```
airflow connections add 'kinetica_default' \
    --conn-type 'kinetica' \
    --conn-login '_default_login' \
    --conn-password '_default_password'  \
    --conn-host 'http://g-p100-300-301-u29.tysons.kinetica.com:9191/'
```

### 3.3. Start Airflow in Standalone mode

You must provide a location that will be used for the `$AIRFLOW_HOME`. We set this in the conda environment.

```sh
(airflow) $ mkdir ./home
(airflow) $ conda env config vars set AIRFLOW_HOME=$PWD/home
(airflow) $ conda activate airflow
(airflow) [home] $ echo $AIRFLOW_HOME
~/fsq-airflow/airflow/standalone
```

When you startup airflow in standalone mode it will copy files into `$AIRFLOW_HOME` if they do not already exist. When startup is complete it will show the admin and user password for the webserver.

```sh
(airflow) [~]$ cd $AIRFLOW_HOME
(airflow) [standalone]$ airflow standalone
[...]
 webserver | [2024-03-07 22:00:34 -0600] [18240] [INFO] Listening at: http://0.0.0.0:8080 (18240)
standalone | Airflow is ready
standalone | Login with username: admin  password: 39FrRzqzRYTK3pc9
standalone | Airflow Standalone is for development purposes only. Do not use this in production!
```

You can edit the `airflow.cfg` file if you need to change any ports.

### 3.5. Example DAGs

Run the [example DAGs](./example_dags) to verify the installation. See the comments in the code for more details.

## 5. See Also

### 5.1 Kinetica Docs

- [Kinetica Python API](https://docs.kinetica.com/7.1/api/python/)
- [Kinetica SQL](https://docs.kinetica.com/7.1/sql/)

### 5.2 Airflow Docs

- [Airflow Quickstart](https://airflow.apache.org/docs/apache-airflow/stable/start.html)
- [Managing Connections](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
- [SQL Operators](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html)

### 5.3 Building a Provider

- [Airflow Provider Sample](https://github.com/astronomer/airflow-provider-sample)
- [Python Build Module](https://pypa-build.readthedocs.io/en/latest/index.html)
- [Setuptools Wheels](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#wheels)
