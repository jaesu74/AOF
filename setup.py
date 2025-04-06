from setuptools import setup, find_packages

setup(
    name="alloneflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'sqlalchemy',
        'reportlab',
        'scikit-learn',
    ],
) 