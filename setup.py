from setuptools import setup

setup(
    name='GraphEmbedding',
    version='0.1',
    description='Techniques for Structurally Graph Embedding.',
    author='Yunfei Song',
    author_email='syfnico@foxmail.com',
    packages=['ge'],
    install_requires=['sklearn', 'torch']
)
