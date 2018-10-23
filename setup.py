from setuptools import find_packages
from setuptools import setup

import versioneer

test_deps = [
    'behave',
    'pytest',
    'pytest-cov',
    'coverage',
    ],
extras = {
    'test': test_deps,
}

setup(
    name = "abaqus2dyna",
    version = versioneer.get_version(),
    cmdclass = versioneer.get_cmdclass(),
    author = "Tim Hartman",
    author_email = "tbhartman@gmail.com",
    description = ("Translator from Abaqus input files to LS-DYNA input files"),
    license = "MIT",
    keywords = "abaqus ls-dyna dyna",
    url = "https://github.com/tbhartman/abaqus2dyna",
    packages=find_packages('src', exclude=['test*']),
    package_dir = {'':'src'},
    entry_points={
        'console_scripts':[
            'abaqus2dyna = abaqus2dyna.__main__:main',
            ],
        },
    install_requires = ['numpy'],
    tests_require = test_deps,
    extras_require = extras,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
