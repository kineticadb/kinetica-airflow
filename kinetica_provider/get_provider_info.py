##
# Copyright (c) 2023, Chad Juliano, Kinetica DB Inc.
##

from importlib.metadata import version

__name__ = "airflow-provider-kinetica"
__version__ = version(__name__)

## This is needed to allow Airflow to pick up specific metadata fields it needs for certain features.
def get_provider_info():
    return {
        "package-name": __name__,  # Required
        "name": "Kinetica Airflow Provider",  # Required
        "description": "This provider has operators and hooks for executing SQL in the Kinetica database.",  # Required

        "description": "`Kinetica DB <https://docs.kinetica.com>`__\n",
        "connection-types": [
            { "connection-type": "kinetica", 
              "hook-class-name": "kinetica_provider.hooks.sql.KineticaSqlHook" }
        ],
        "extra-links": ["kinetica_provider.operator.spark.KineticaSparkLink"],
        "versions": [__version__],  # Required
    }
