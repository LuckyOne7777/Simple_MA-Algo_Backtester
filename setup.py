from setuptools import setup, find_packages

setup(
    name='simple_algo_backtester',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'matplotlib',
        'yfinance'
    ],
)
