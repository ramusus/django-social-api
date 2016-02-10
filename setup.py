from setuptools import setup, find_packages

setup(
    name='django-social-api',
    version=__import__('social_api').__version__,
    description='Django social networks API abstraction layer',
    long_description=open('README.md').read(),
    author='ramusus',
    author_email='ramusus@gmail.com',
    url='https://github.com/ramusus/django-social-api',
    download_url='http://pypi.python.org/pypi/django-social-api',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # because we're including media that Django needs
    install_requires=[
        'distributedlock',
        'requests',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
