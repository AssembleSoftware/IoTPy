import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="iotpy", # Replace with your own username
    version="1.0.0",
    author="Mani Chandy",
    author_email="",
    description="IoTPy - Python for Streams",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AssembleSoftware/IoTPy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
