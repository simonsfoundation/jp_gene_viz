# jp_gene_viz

A collection of visualizations for genomics related information for use with Jupyter notebooks.

Please see the [index.ipynb](index.ipynb) IPython notebook for
a guide to the package content.

To launch a container to run the package in the Binder service, please
click the image link below:

[![Binder](http://mybinder.org/badge.svg)](http://mybinder.org/repo/simonsfoundation/jp_gene_viz)

# Installation

The installation requires the Python module `jp_gene_viz` to be installed with its
dependencies and for the wigdets extension to be enabled in Jupyter/IPython.

For example the following sequence completes a first time complete installation

### install prerequisites

You will need Python 2.7 and some other libraries for the installation
to succeed.  I recommend installing 
[Anaconda for python 2.7](https://www.continuum.io/downloads) to get all
needed prerequisite dependencies.

### Linux only:

On Debian Linux without using Anaconda I needed to add the following system
libraries

```
sudo apt-get install python-pip
sudo apt-get install python-dev
sudo apt-get install -y libigraph0-dev 
sudo apt-get install libxml2-dev
sudo apt-get install zlib1g-dev
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
```

### clone the repository and change directory into the repository folder

```
git clone https://github.com/simonsfoundation/jp_gene_viz.git
cd jp_gene_viz
```

### Linux and Mac: install the requirements and the module
```
pip install -r requirements.txt
python setup.py install
```

### Mac notes

For some Macs the `pip` install of requirements fails to install `python-igraph`.
If this happens use [homebrew](https://brew.sh/) to install the `igraph` library
```
brew install igraph
```
and then run the `pip` install again.

### Windows install

To install for windows the `python-igraph` package must be installed in a separate step.
to to [http://www.lfd.uci.edu/~gohlke/pythonlibs/#python-igraph](http://www.lfd.uci.edu/~gohlke/pythonlibs/#python-igraph) to get
`python_igraph‑0.7.1.post6‑cp27‑cp27m‑win_amd64.whl` and then install using a command
similar to

```
python -m pip install Downloads\python_igraph-0.7.1.post6-cp27-cp27m-win_amd64.whl
```

Then install the remaining components

```
pip install -r windows_requirements.txt 
python setup.py install
```

### enable the widgets extension (just in case it isn't already enabled)
```
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

Note: We are upgrading the repository to work with the latest ipywidgets and iPython
releases.  If you have problems installing the package please post an issue at
[https://github.com/simonsfoundation/jp_gene_viz](https://github.com/simonsfoundation/jp_gene_viz).

