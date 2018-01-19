FROM andrewosh/binder-base

MAINTAINER Aaron Watters <awatters@simonsfoundation.org>

USER main

RUN git clone https://github.com/simonsfoundation/jp_gene_viz.git repo
RUN cd repo; pip install -r requirements.txt
RUN cd repo; python setup.py install
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension