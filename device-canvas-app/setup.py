from setuptools import setup, find_packages

setup(
    name='device-canvas-app',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A PyQt application for managing device objects on a canvas.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'PyQt5',
    ],
    entry_points={
        'console_scripts': [
            'device-canvas-app=main:main',  # Adjust the entry point as necessary
        ],
    },
)