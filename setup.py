from setuptools import setup, find_packages

setup(
    name='labelsgen',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'qrcode',
        'reportlab',
    ],
    entry_points={
        'console_scripts': [
            'labelsgen = labelsgen:main',
        ],
    },
)
