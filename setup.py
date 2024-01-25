from setuptools import setup, find_packages

setup(
    name='cnl2asp',
    version='1.2.0',
    description='A tool for converting a Controlled Natural Language based on English into Answer Set Programming',
    url='https://github.com/dodaro/cnl2asp/tree/refactoring',
    license='Apache License',
    author='Carmine Dodaro',
    author_email='carmine.dodaro@unical.it',
    maintainer='Simone Caruso',
    maintainer_email='simone.caruso@edu.unige.it',
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['test*']),
    package_data={'': ['grammar.lark']},
    install_requires=['lark', 'inflect'],
    python_requires=">=3.10"
)