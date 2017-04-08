import os.path as osp

from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()

setup(
    name='KegLogin',
    setup_requires=[
        'setuptools_scm',
    ],
    use_scm_version=True,
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
        'Flask-Login',
        'Keg',
        'KegElements'
    ],
    long_description=README,
)
