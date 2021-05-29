import setuptools
import os

config_d_filepath = os.path.join(
    'jupyter-config', 'jupyter_notebook_config.d', 'zebrafish_on_jupyter.json'
)
data_files = [('etc/jupyter/jupyter_notebook_config.d', [config_d_filepath])]

setuptools.setup(
    name="zebrafish_on_jupyter",
    version='0.1.4',
    author="Yunjae Choi",
    author_email="yunjae.choi1000@gmail.com",
    description="Extension for the jupyter notebook server for zebrafish",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['notebook'],
    data_files=data_files,
    entry_points={'console_scripts': ['jupyter-zebrafish = zebrafish_on_jupyter.zebrafishapp:main']},
)
