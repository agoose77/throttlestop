from setuptools import setup, find_packages

setup(
    name='throttlestop',
    version='0.0.1',
    install_requires=['plumbum', 'numpy'],
    url='https://github.com/agoose77/throttlestop',
    license='',
    author='Angus Hollands',
    author_email='goosey15@gmail.com',
    description='Simple tool to manage throttling problems on Linux',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'throttlestop = throttlestop:main',
            'throttlestop-install-service = throttlestop.install:main',
        ],
    },
)
