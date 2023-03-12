# mypy: ignore_errors=True
# pylint: disable=invalid-name

from setuptools import setup

version = {}
with open("filament_info/fse_version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=exec-used

try:
    import octoprint_setuptools
except ModuleNotFoundError:
    print(
        "Could not import OctoPrint's setuptools, are you sure you are "
        "running that under the same python installation that OctoPrint "
        "is installed under?"
    )
    import sys
    sys.exit(-1)

plugin_identifier = "filament_info"
plugin_package = "filament_info"
plugin_name = "Filament Info"
plugin_version = version['VERSION']
plugin_description = ("Plugin for integrating a load cell into a filament "
                      "holder.")
plugin_author = "Mateusz Przytuła"
plugin_author_email = "mateusz.przytula@vp.pl"
plugin_url = "https://github.com/Techman83/Filament-Scale-Enhanced"
plugin_license = "AGPLv3"
plugin_requires = ["RPi.GPIO", "spidev", "mfrc522"]
plugin_extras_require = {
    'development': [
        'autopep8',
        'pytest',
        'pytest-mypy',
        'mypy',
        'pytest-pylint',
        'pylint',
        'pytest-flake8',
        'Mock.GPIO'
    ],
    'test': [
        'pytest',
        'pytest-mypy',
        'mypy',
        'pytest-pylint',
        'pylint',
        'pytest-flake8',
        'Mock.GPIO'
    ]
}

plugin_additional_data = []
plugin_additional_packages = []
plugin_ignored_packages = []
additional_setup_parameters = {}

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data,
    extra_requires=plugin_extras_require
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge
    setup_parameters = dict_merge(setup_parameters,
                                  additional_setup_parameters)

setup(**setup_parameters)
