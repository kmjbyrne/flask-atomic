from setuptools import find_packages
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='Flask-Atomic',
    version='0.1.8',
    description='Core code for Flask based projects',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='python library utilities',
    url='https://github.com/kmjbyrne/flask-atomic',
    author='Keith Byrne',
    author_email='keithmbyrne@gmail.com',
    license='MIT',
    packages=find_packages(exclude=('tests', )),
    install_requires=[
        'markdown',
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3', 'coverage'],
    include_package_data=True,
    zip_safe=True
)
