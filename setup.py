from setuptools import setup, find_packages

setup(
    name="stock-financial-analysis",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "akshare>=1.10.0",
        "yfinance>=0.2.0",
        "requests>=2.26.0",
        "urllib3>=1.26.0",
    ],
    python_requires=">=3.8",
)
