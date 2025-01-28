# mRNABench
This repository contains a workflow to benchmark the embedding quality of genomic foundation models on (m)RNA specific tasks. The mRNABench contains a catalogue of datasets and training split logic which can be used to evaluate the embedding quality of several catalogued models.

**Jump to:** [Model Catalog](#model-catalog) [Dataset Catalog](#dataset-catalog)

## Setup
Several configurations of the mRNABench are available.

### Datasets Only
If you are interested in the benchmark datasets **only**, you can run:

```bash
pip install mrna-bench
```

### Full Version
The inference-capable version of mRNABench that can generate embeddings using
Orthrus, DNA-BERT2, NucleotideTransformer, RNA-FM, and HyenaDNA can be 
installed as shown below. Note that this requires PyTorch version 2.2.2 with 
CUDA 12.1 and Triton uninstalled (due to a DNA-BERT2 issue).
```bash
conda create --name mrna_bench python=3.10
conda activate mrna_bench

pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cu121
pip install mrna-bench[base_models]
pip uninstall triton
```
Inference with other models will require the installation of the model's
dependencies first, which are usually listed on the model's GitHub page (see below).

### Post-install
After installation, please run the following in Python to set where data associated with the benchmarks will be stored.
```python
import mrna_bench as mb

path_to_dir_to_store_data = "DESIRED_PATH"
mb.update_data_path(path_to_dir_to_store_data)
```

## Usage
Datasets can be retrieved using:

```python
import mrna_bench as mb

dataset = mb.load_dataset("go-mf")
data_df = dataset.data_df
```

The mRNABench can also be used to test out common genomic foundation models:
```python
import torch

import mrna_bench as mb
from mrna_bench.embedder import DatasetEmbedder
from mrna_bench.linear_probe import LinearProbe

device = torch.device("cuda")

dataset = mb.load_dataset("go-mf")
model = mb.load_model("Orthrus", "orthrus-large-6-track", device)

embedder = DatasetEmbedder(model, dataset)
embeddings = embedder.embed_dataset()
embeddings = embeddings.detach().cpu().numpy()

prober = LinearProbe(
    dataset=dataset,
    embeddings=embeddings,
    task="multilabel",
    target_col="target",
    split_type="homology"
)

metrics = prober.run_linear_probe()
print(metrics)
```
Also see the `scripts/` folder for example scripts that uses slurm to embed dataset chunks in parallel for reduce runtime, as well as an example of multi-seed linear probing.

## Model Catalog
The current models catalogued are shown below. Currently, all models but AIDO.RNA are supported by the `base_models` optional installation.

| Model Name |  Model Versions         | Description   | Citation |
| :--------: |  ---------------------- | ------------- | :------: | 
| `Orthrus` | `orthrus-large-6-track`<br> `orthrus-base-4-track` | Mamba-based RNA FM pre-trained using contrastive learning. | [[Code]](https://github.com/bowang-lab/Orthrus) [[Paper]](https://www.biorxiv.org/content/10.1101/2024.10.10.617658v2)|
| `AIDO.RNA` | `aido_rna_650m` <br> `aido_rna_650m_cds` <br> `aido_rna_1b600m` <br> `aido_rna_1b600m_cds` | Encoder Transformer-based RNA FM pre-trained using MLM on 42M ncRNA sequences. Version that is domain adapted to CDS is available. | [[Paper]](https://www.biorxiv.org/content/10.1101/2024.11.28.625345v1) |
| `RNA-FM` | `rna-fm` <br> `mrna-fm` | Transformer-based RNA FM pre-trained using MLM on 23M ncRNA sequences. mRNA-FM trained on CDS using codon tokenizer. | [[Github]](https://github.com/ml4bio/RNA-FM) |
| `DNABERT2` | `dnabert2` | Transformer-based DNA FM pre-trained using MLM on multispecies genomic dataset. Uses BPE and other modern architectural improvements for efficiency. | [[Github]](https://github.com/MAGICS-LAB/DNABERT_2) |
| `Nucleotide`<br>`Transformer` | `2.5b-multi-species` <br> `2.5b-1000g` <br> `500m-human-ref` <br> `500m-1000g` <br> `v2-50m-multi-species` <br> `v2-100m-multi-species` <br> `v2-250m-multi-species` <br> `v2-500m-multi-species` | Transformer-based DNA FM pre-trained using MLM on a variety of possible datasets at various model sizes. Sequence is tokenized using 6-mers. | [[Github]](https://github.com/instadeepai/nucleotide-transformer) |
| `HyenaDNA` | `hyenadna-large-1m-seqlen-hf` <br> `hyenadna-medium-450k-seqlen-hf` <br> `hyenadna-medium-160k-seqlen-hf` <br> `hyenadna-small-32k-seqlen-hf` <br> `hyenadna-tiny-16k-seqlen-d128-hf` | Hyena-based DNA FM pre-trained using NTP on the human reference genome. Available at various model sizes and pretraining sequence contexts. | [[Github]](https://github.com/HazyResearch/hyena-dna) |
| `SpliceBERT` | `SpliceBERT.1024nt` <br> `SpliceBERT-human.510nt` <br> `SpliceBERT.510nt` |  Transformer-based RNA foundation model trained on 2 million vertebrate RNA sequences using a MLM pretraining objective. Alternative versions are trained on only human RNA, and using smaller context windows. | [[Github]](https://github.com/chenkenbio/SpliceBERT) |
| `RiNALMo` | `rinalmo` | RiNALMo is a transformer-based RNA foundation model trained on 36M ncRNA sequences using MLM and other modern architectural improvements such as RoPE, SwiGLU activations, and Flash Attention. | [[Github]](https://github.com/lbcb-sci/RiNALMo) |
| `UTR-LM` | `utrlm-te_el` <br> `utrlm-mrl` | UTR-LM is a transformer-based RNA foundation model that is pre-trained on random and endogenous 5'UTR sequences from various species using MLM. | [[Github]](https://github.com/a96123155/UTR-LM) |


<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Model Versions</th>
      <th style="width: 300px;">Description</th>
      <th>Citation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>Orthrus</code></td>
      <td><code>orthrus-large-6-track</code><br><code>orthrus-base-4-track</code></td>
      <td>Mamba-based RNA FM pre-trained using contrastive learning.</td>
      <td>
        <a href="https://github.com/bowang-lab/Orthrus">[Code]</a>
        <br>
        <a href="https://www.biorxiv.org/content/10.1101/2024.10.10.617658v2">[Paper]</a>
      </td>
    </tr>
    <tr>
      <td><code>AIDO.RNA</code></td>
      <td><code>aido_rna_650m</code><br><code>aido_rna_650m_cds</code><br><code>aido_rna_1b600m</code><br><code>aido_rna_1b600m_cds</code></td>
      <td>
        Encoder Transformer-based RNA FM pre-trained using MLM on 42M ncRNA sequences. Domain-adapted version for CDS is available.
      </td>
      <td>
        <a href="https://www.biorxiv.org/content/10.1101/2024.11.28.625345v1">[Paper]</a>
      </td>
    </tr>
    <tr>
      <td>RNA-FM</td>
      <td><code>rna-fm</code><br><code>mrna-fm</code></td>
      <td>
        Transformer-based RNA FM pre-trained using MLM on 23M ncRNA sequences. mRNA-FM trained on CDS using codon tokenizer.
      </td>
      <td>
        <a href="https://github.com/ml4bio/RNA-FM">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>DNABERT2</td>
      <td><code>dnabert2</code></td>
      <td>
        Transformer-based DNA FM pre-trained using MLM on multispecies genomic datasets. Uses BPE and other architectural improvements for efficiency.
      </td>
      <td>
        <a href="https://github.com/MAGICS-LAB/DNABERT_2">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>Nucleotide<br>Transformer</td>
      <td>
        <code>2.5b-multi-species</code><br>
        <code>2.5b-1000g<br>500m-human-ref</code><br>
        <code>500m-1000g</code><br>
        <code>v2-50m-multi-species</code><br>
        <code>v2-100m-multi-species</code><br>
        <code>v2-250m-multi-species</code><br>
        <code>v2-500m-multi-species</code>
      </td>
      <td>
        Transformer-based DNA FM pre-trained using MLM on various datasets at different sizes. Sequence tokenized using 6-mers.
      </td>
      <td>
        <a href="https://github.com/instadeepai/nucleotide-transformer">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>HyenaDNA</td>
      <td>
        <code>hyenadna-large-1m-seqlen-hf</code><br>
        <code>hyenadna-medium-450k-seqlen-hf</code><br>
        <code>hyenadna-medium-160k-seqlen-hf</code><br>
        <code>hyenadna-small-32k-seqlen-hf</code><br>
        <code>hyenadna-tiny-16k-seqlen-d128-hf</code>
      </td>
      <td>
        Hyena-based DNA FM pre-trained using NTP on the human reference genome. Available at various model sizes and pretraining sequence contexts.
      </td>
      <td>
        <a href="https://github.com/HazyResearch/hyena-dna">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>SpliceBERT</td>
      <td>
        <code>SpliceBERT.1024nt</code><br>
        <code>SpliceBERT-human.510nt</code><br>
        <code>SpliceBERT.510nt</code>
      </td>
      <td>
        Transformer-based RNA FM trained on 2 million vertebrate RNA sequences using MLM. Variants are trained on human RNA or smaller context windows.
      </td>
      <td>
        <a href="https://github.com/chenkenbio/SpliceBERT">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>RiNALMo</td>
      <td><code>rinalmo</code></td>
      <td>
        Transformer-based RNA FM trained on 36M ncRNA sequences using MLM and modern improvements such as RoPE, SwiGLU activations, and Flash Attention.
      </td>
      <td>
        <a href="https://github.com/lbcb-sci/RiNALMo">[Github]</a>
      </td>
    </tr>
    <tr>
      <td>UTR-LM</td>
      <td><code>utrlm-te_el</code><br>
      <code>utrlm-mrl</code></td>
      <td>
        Transformer-based RNA FM pre-trained on random and endogenous 5'UTR sequences from various species using MLM.
      </td>
      <td>
        <a href="https://github.com/a96123155/UTR-LM">[Github]</a>
      </td>
    </tr>
  </tbody>
</table>

### Adding a new model
All models should inherit from the template `EmbeddingModel`. Each model file should lazily load dependencies within its `__init__` methods so each model can be used individually without install all other models. Models must implement `get_model_short_name(model_version)` which fetches the internal name for the model. This must be unique for every model version and must not contain underscores. Models should implement either `embed_sequence` or `embed_sequence_sixtrack` (see code for method signature). New models should be added to `MODEL_CATALOG`.

## Dataset Catalog
The current datasets catalogued are:
| Dataset Name | Catalogue Identifier | Description | Tasks | Citation |
|---|---|---|---|---|
| GO Molecular Function | <code>go-mf</code> | Classification of the molecular function of a transcript's  product as defined by the GO Resource. | `multilabel` | [website](https://geneontology.org/) |
| Mean Ribosome Load (Sugimoto) | <code>mrl&#8209;sugimoto</code> | Mean Ribosome Load per transcript isoform as measured in Sugimoto et al. 2022. | `regression` | [paper](https://www.nature.com/articles/s41594-022-00819-2) |
| RNA Half-life (Human) | <code>rnahl&#8209;human</code> | RNA half-life of human transcripts collected by Agarwal et al. 2022. | `regression` | [paper](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-022-02811-x) |
| RNA Half-life (Mouse) | <code>rnahl&#8209;mouse</code> | RNA half-life of mouse transcripts collected by Agarwal et al. 2022. | `regression` | [paper](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-022-02811-x) |
| Protein Subcellular Localization | <code>prot&#8209;loc</code> | Subcellular localization of transcript protein product defined in Protein Atlas. | `multilabel` | [website](https://www.proteinatlas.org/) |
| Protein Coding Gene Essentiality | <code>pcg&#8209;ess</code> | Essentiality of PCGs as measured by CRISPR knockdown. Log-fold expression and binary essentiality available on several cell lines. | `regression` `classification`| [paper](https://www.cell.com/cell/fulltext/S0092-8674(24)01203-0)|

### Adding a new dataset
New datasets should inherit from `BenchmarkDataset`. Dataset names cannot contain underscores. Each new dataset should download raw data and process it into a dataframe by overriding `process_raw_data`. This dataframe should store transcript as rows, using string encoding in the `sequence` column. If homology splitting is required, a column `gene` containing gene names is required. Six track embedding also requires columns `cds` and `splice`. The target column can have any name, as it is specified at time of probing. New datasets should be added to `DATASET_CATALOG`.
