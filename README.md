## Minimal Paper Manager

### What is this ?

- Extract titles and abstracts from papers
- Save extracted information as catalog csv file

You can manage your collected papers with this catalog file.

### How to use

##### Preparation
1. Install required packages
    ```
    $ pip install -r requirements.txt
    ```
1. Put your all papers in a folder
    ```
    sample_papers
    │   1512.03385.pdf
    │
    └───Transformer
    │   │   1706.03762.pdf
    │
    └───GAN
        │   1406.2661.pdf
    ```
    You can place papers into subfolders.


##### Make catalog
```
$ python make_catalog.py YOUR_PAPERS_ROOT_DIRECTORY
```

In the example above, you will run
```
$ python make_catalog.py sample_papers
```

You'll get a following catalog csv.
```
>>> import pandas as pd
>>> df = pd.read_csv("catalog.csv")
>>> df.head()
         filename      dirpath                                         title                                           abstract                                           filepath
0  1512.03385.pdf          NaN  Deep Residual Learning for Image Recognition  Deeper neural networks are more difﬁcult to tr...  /path/to/sample_papers/1512.03385.pdf
1   1406.2661.pdf          GAN                   Generative Adversarial Nets  We propose a new framework for estimating gene...  /path/to/sample_papers/GAN/1406.2661.pdf
2  1706.03762.pdf  Transformer                     Attention Is All You Need  The dominant sequence transduction models are ...  /path/to/sample_papers/Transformer/1706.03762.pdf
```

You can find some options by `$ python make_catalog.py -h`.

### License
MIT
