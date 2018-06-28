from setuptools import setup, find_packages

with open('LICENSE') as f:
    license = f.read()

with open('README.rst') as f:
    readme = f.read()

setup(
    name="daikin-arc466",
    version="0.0.dev0",
    author="Javier de la Puente",
    author_email="jdelapuentealonso@gmail.com",
    description=("Library to use the remote control for Daikin model ARC466A6"),
    license=license,
    keywords="Daikin ARC466A",
    url="http://www.javierdelapuente.com",
    packages=find_packages(exclude=('tests', 'docs', 'examples', 'real_frames')),
    long_description=readme,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Home Automation",
        "License :: OSI Approved :: MIT License", 
    ],
)
