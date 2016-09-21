import os

from setuptools import setup, find_packages

from keg_login.version import VERSION

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()

setup(
    name='KegLogin',
    version=VERSION,
    description='Authentication views for Keg',
    author='Level 12',
    author_email='devteam@level12.io',
    url='https://github.com/level12/keg-login',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[

    ],
    long_descripton=README,
)