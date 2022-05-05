#!/usr/bin/env python -i

# Invoke this with, for example,
#
#   python -i interactor.py ~/scdata/anndata/pbmc-small.h5ad
#
# -- then you can inspect the anndata object.

import tiledb
import tiledbsc
import sys, os

import anndata

import pandas
import numpy
import scipy

input_path = 'anndata/pbmc3k_processed.h5ad'
if len(sys.argv) != 2:
    print(f"{sys.argv[0]}: need just one .h5ad file name.", file=sys.stderr)
    sys.exit(1)

input_path  = sys.argv[1]
a = anndata.read_h5ad(input_path)

# Interact at the prompt now:
# * a.X
# * a.obs.keys()
# * a.obs.head()
# * a.obs.index
# * a.obs.values
# * etc
