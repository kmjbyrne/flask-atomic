from setuptools import setup
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='Flask-KBPC',
    version='0.2.0',
    description='Reusable Python code for projects',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='python library utilities',
    url='https://github.com/kmjbyrne/kbpc',
    author='Keith Byrne',
    author_email='keithmbyrne@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'markdown',
    ],

    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    entry_points={
        # 'console_scripts': ['funniest-joke=funniest.command_line:main'],
    },
    include_package_data=True,
    zip_safe=False
)
