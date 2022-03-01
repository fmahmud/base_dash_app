from setuptools import find_packages, setup
setup(
    name='base_dash_app',
    packages=find_packages(),
    version='0.2.1',
    description='Base Dash Webapp',
    author='fmahmud',
    license='MIT',
    install_requires=[
        'dash', 'dash-bootstrap-components', 'dash-core-components', 'dash-html-components',
        'Flask', 'Flask-Compress', 'requests', 'SQLAlchemy', 'trueskill', 'urllib3'
    ]
)
