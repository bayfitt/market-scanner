"""Setup script for Market Scanner"""

from setuptools import setup, find_packages
import os

# Read version
def get_version():
    with open(os.path.join(os.path.dirname(__file__), '__init__.py'), 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.0.0'

# Read requirements
def get_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='market-scanner',
    version=get_version(),
    description='Autonomous Market Scanner - Find symbols guaranteed to outperform BTC',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='Market Scanner Team',
    author_email='scanner@example.com',
    url='https://github.com/your-username/market-scanner',
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements(),
    entry_points={
        'console_scripts': [
            'market-scanner=market_scanner.cli:main',
            'mscan=market_scanner.cli:main',  # Short alias
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.8',
    keywords='trading, stocks, market, scanner, bitcoin, technical-analysis',
    project_urls={
        'Bug Reports': 'https://github.com/your-username/market-scanner/issues',
        'Source': 'https://github.com/your-username/market-scanner',
    },
)