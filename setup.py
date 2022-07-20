from distutils.core import setup

setup(
    # Application name:
    name="Simple Scheduler",
    
    # Version number (initial):
    version="0.0.1",
    
    # Application author details:
    author="Quentin Bullock",
    
    # Packages
    packages=["simple_scheduler"],
    
    # Include additional files into the package
    include_package_data=True,
    
    # Details
    url="http://pypi.python.org/pypi/MyApplication_v010/",
    
    #
    # license="LICENSE.txt",
    description="A basic scheduler",
    
    # long_description=open("README.txt").read(),
    
    # Dependent packages (distributions)
    install_requires=[
        'pycron',
        'sqlite_utils'
    ],
)