from textwrap import dedent

from setuptools import setup, find_packages

setup(
    name='cnl2asp',
    version='1.3.14',
    description='A tool for converting a Controlled Natural Language based on English into Answer Set Programming',
    long_description=dedent('''\
                            A tool for converting a Controlled Natural Language based on English into Answer Set Programming
                            
                            Documentation is available at:
                            https://dodaro.github.io/cnl2asp/
                            '''),
    url='https://github.com/dodaro/cnl2asp/tree/main',
    license='Apache License',
    author='Carmine Dodaro',
    author_email='carmine.dodaro@unical.it',
    maintainer='Simone Caruso',
    maintainer_email='simone.caruso@edu.unige.it',
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['tests*']),
    package_data={'': ['grammar.lark']},
    install_requires=['lark', 'inflect', 'multipledispatch'],
    entry_points={
        'console_scripts': ['cnl2asp = cnl2asp.cnl2asp:main'],
    },
    python_requires=">=3.10"
)