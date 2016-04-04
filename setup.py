from setuptools import setup, Extension

setup(
        name='snap7zero',
        version='0.1.1',
        packages=['snap7zero'],
        url='https://github.com/SimplyAutomationized/snap7zero',
        license='',
        author='SimplyAutomationized',
        author_email='nextabyte@gmail.com',
        description='snap7-python helper library',
        install_requires=["twisted","python-snap7","ujson","gpiozero"],

)
