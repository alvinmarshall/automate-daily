from setuptools import setup, find_packages

setup(
    name='automate-daily',
    version='1.0.0',
    url='',
    license='MIT',
    scripts=['install.sh'],
    author='bik_krlvn',
    packages=find_packages(include=['timecard', 'main.*']),
    author_email='kelvin@migmeninfo.com',
    description='Daily time card utility',
    package_data={'timecard': ['serviceacct_spreadsheet.json']},
    include_package_data=True,
    install_requires=[
        'gspread==4.0.1',
        'google-auth==2.3.0',
        'pyinquirer==1.0.3'
    ],
    entry_points={
        'console_scripts': ['timecard=timecard.main:main']
    }
)
