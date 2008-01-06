#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='Pastie',
    version='0.0.1',
    description='Pastebin',
    author='Pedro Algarvio',
    author_email='ufs@ufsoft.org',
    url='http://pastie.ufsoft.org',
    #install_requires=["Pylons>=0.9.6"],
    install_requires=["Pylons>=0.9.6", "pygments", "Genshi", "SQLAlchemy",
                      "PylonsGenshi"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'pastie': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors = {'pastie': [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},
    entry_points="""
    [paste.app_factory]
    main = pastie.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
