from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='kbpc',
    version='0.1',
    description='Reusable Python code for projects',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='python library utilities',
    url='http://github.com/kmjbyrne/kbpc',
    author='Keith Byrne',
    author_email='keithmbyrne@gmail.com',
    license='MIT',
    packages=['kbpc'],
    # install_requires=[
    #     'markdown',
    # ],
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    entry_points={
        # 'console_scripts': ['funniest-joke=funniest.command_line:main'],
    },
    include_package_data=True,
    zip_safe=False
)
