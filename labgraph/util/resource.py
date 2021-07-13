#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import pkgutil
import sys
import tempfile
import zipimport


def get_resource_tempfile(package: str, resource: str) -> str:
    """
    Returns a filename for a resource. Works even in zipped packages.

    Args:
        package: The package the resource is contained in.
        resource: The name of the resource.
    """
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
        try:
            data = pkgutil.get_data(package, resource)
            assert data is not None
            temp_file.write(data)
        except (NotADirectoryError, FileNotFoundError):
            if sys.argv[0].endswith(".pex"):
                pex_path = sys.argv[0]
            elif sys.argv[1].endswith(".pex"):
                pex_path = sys.argv[1]
            else:
                raise
            zip_importer = zipimport.zipimporter(pex_path)
            temp_file.write(
                zip_importer.get_data(  # type: ignore
                    package.replace(".", "/") + "/" + resource
                )
            )
    return temp_file.name
