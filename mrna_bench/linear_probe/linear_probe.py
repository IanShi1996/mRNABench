import json
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

from sklearn.base import RegressorMixin, ClassifierMixin
from sklearn.linear_model import RidgeCV, LinearRegression, LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from mrna_bench import load_dataset
from mrna_bench.data_splitter.data_splitter import DataSplitter
from mrna_bench.data_splitter.split_catalog import SPLIT_CATALOG
from mrna_bench.datasets import BenchmarkDataset
from mrna_bench.models import EmbeddingModel, MODEL_CATALOG
from mrna_bench.embedder import get_output_filepath


class LinearProbe:
    """Linear Probe Evaluation Module.

    Performs linear probing on embeddings for sequences from a benchmark
    dataset generated by an embedding model. The linear probing task can
    be selected at initialization on a target column from the benchmarking
    dataset dataframe.

    The train and test splits for linear probing can be recomputed from random
    seeds. This module supports generating splits based on sequence gene name
    homology from homologene.
    """

    linear_models = {
        "regression": RidgeCV(alphas=[1e-3, 1e-2, 1e-1, 1, 10]),
        "reg_lin": LinearRegression(),
        "reg_ridge": RidgeCV(alphas=[1e-3, 1e-2, 1e-1, 1, 10]),
        "classification": LogisticRegression(max_iter=5000),
        "multilabel": MultiOutputClassifier(
            LogisticRegression(max_iter=5000)
        )
    }

    @staticmethod
    def load_persisted_embeddings(
        embedding_dir: str,
        model_short_name: str,
        dataset_name: str,
        seq_overlap: int = 0
    ) -> np.ndarray:
        """Load pre-computed embeddings for dataset from persisted location.

        Args:
            embedding_dir: Directory where embedding is stored.
            model_short_name: Shortened name of embedding model version.
            dataset_name: Name of dataset which was embedded.
            seq_overlap: Sequence chunking overlap used during embedding.

        Returns:
            Embeddings for dataset computed using embedding model.
        """
        embeddings_fn = get_output_filepath(
            embedding_dir,
            model_short_name,
            dataset_name,
            seq_overlap,
        ) + ".npz"

        embeddings = np.load(embeddings_fn)["embedding"]
        return embeddings

    @classmethod
    def init_from_instance(
        cls,
        model: EmbeddingModel,
        dataset: BenchmarkDataset,
        task: str,
        target_col: str,
        seq_chunk_overlap: int = 0,
        split_type: str = "homology",
        split_ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
        eval_all_splits: bool = False
    ) -> "LinearProbe":
        """Initialize LinearProbe from instantiated dataset and model.

        Args:
            model: EmbeddingModel that generated embeddings to be probed.
            dataset: BenchmarkDataset containing embedded sequences.
            task: Linear probing task. Valid tasks: {"regression", "reg_lin",
                "reg_ridge", "classification", "multilabel"}.
            target_col: Column from dataframe to use as labels.
            seq_chunk_overlap: Sequence chunk overlap used during embedding.
            split_type: Method used for data split generation. Valid types:
                {"default", "homology"}.
            split_ratios: Ratio of data split sizes as a fraction of dataset.
            eval_all_splits: Evaluate metrics on all splits. Only evaluates
                validation split otherwise.

        Returns:
            Initialized LinearProbe.
        """
        embeddings = cls.load_persisted_embeddings(
            dataset.embedding_dir,
            model.short_name,
            dataset.dataset_name,
            seq_chunk_overlap
        )
        return cls(
            dataset,
            model.short_name,
            seq_chunk_overlap,
            embeddings,
            task,
            target_col,
            split_type,
            split_ratios,
            eval_all_splits
        )

    @classmethod
    def init_from_name(
        cls,
        model_name: str,
        model_version: str,
        dataset_name: str,
        task: str,
        target_col: str,
        seq_chunk_overlap: int = 0,
        split_type: str = "homology",
        split_ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
        eval_all_splits: bool = False
    ) -> "LinearProbe":
        """Initialize LinearProbe using model and dataset names.

        Args:
            model_name: Name of model to be probed.
            model_version: Version of model to be probed.
            dataset_name: Name of dataset containing embedded sequences.
            task: Linear probing task. Valid tasks: {"regression", "reg_lin",
                "reg_ridge", "classification", "multilabel"}.
            target_col: Column from dataframe to use as labels.
            seq_chunk_overlap: Sequence chunk overlap used during embedding.
            split_type: Method used for data split generation. Valid types:
                {"default", "homology"}.
            split_ratios: Ratio of data split sizes as a fraction of dataset.
            eval_all_splits: Evaluate metrics on all splits. Only evaluates
                validation split otherwise.

        Returns:
            Initialized LinearProbe.
        """
        model_class = MODEL_CATALOG[model_name]
        model_short_name = model_class.get_model_short_name(model_version)

        dataset = load_dataset(dataset_name)

        embeddings = cls.load_persisted_embeddings(
            dataset.embedding_dir,
            model_short_name,
            dataset_name,
            seq_chunk_overlap
        )

        return cls(
            dataset,
            model_short_name,
            seq_chunk_overlap,
            embeddings,
            task,
            target_col,
            split_type,
            split_ratios,
            eval_all_splits
        )

    @classmethod
    def init_from_embedding(
        cls,
        embedding_name: str,
        task: str,
        target_col: str,
        split_type: str = "homology",
        split_ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
        eval_all_splits: bool = False
    ) -> "LinearProbe":
        """Initialize LinearProbe from embedding file name.

        Assumes embedding is located in the directory generated by mb's
        embedding module.

        Args:
            embedding_name: Name of embedding file.
            task: Linear probing task. Valid tasks: {"regression", "reg_lin",
                "reg_ridge", "classification", "multilabel"}.
            target_col: Column from dataframe to use as labels.
            seq_chunk_overlap: Sequence chunk overlap used during embedding.
            split_type: Method used for data split generation. Valid types:
                {"default", "homology"}.
            split_ratios: Ratio of data split sizes as a fraction of dataset.
            eval_all_splits: Evaluate metrics on all splits. Only evaluates
                validation split otherwise.

        Returns:
            Initialized LinearProbe.
        """
        emb_fn_arr = embedding_name.split("_")

        dataset_name = emb_fn_arr[0]
        model_short_name = emb_fn_arr[1]
        seq_chunk_overlap = int(emb_fn_arr[2][1:].replace(".npz", ""))

        dataset = load_dataset(emb_fn_arr[0])

        embeddings = cls.load_persisted_embeddings(
            dataset.embedding_dir,
            model_short_name,
            dataset_name,
            seq_chunk_overlap
        )

        return cls(
            dataset,
            model_short_name,
            seq_chunk_overlap,
            embeddings,
            task,
            target_col,
            split_type,
            split_ratios,
            eval_all_splits
        )

    def __init__(
        self,
        dataset: BenchmarkDataset,
        model_short_name: str,
        seq_chunk_overlap: int,
        embeddings: np.ndarray,
        task: str,
        target_col: str,
        split_type: str = "homology",
        split_ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
        eval_all_splits: bool = False,
        **kwargs # noqa
    ):
        """Initialize LinearProbe.

        Args:
            dataset: Dataset containing sequences to be linear probed.
            model_short_name: Name of model used to generate embedding.
            seq_chunk_overlap: Sequence overlap used to generate embedding.
            embeddings: Embeddings of dataset sequences to be probed.
            task: Linear probing task. Valid tasks: {"regression", "reg_lin",
                "reg_ridge", "classification", "multilabel"}.
            target_col: Column from dataframe to use as labels.
            split_type: Method used for data split generation. Valid types:
                {"default", "homology"}.
            split_ratios: Ratio of data split sizes as a fraction of dataset.
            eval_all_splits: Evaluate metrics on all splits. Only evaluates
                validation split otherwise.
        """
        self.dataset = dataset
        self.data_df = dataset.data_df

        self.model_short_name = model_short_name
        self.seq_chunk_overlap = seq_chunk_overlap

        self.task = task
        self.target_col = target_col

        self.concat_embeddings(embeddings)

        self.splitter: DataSplitter

        self.split_type = split_type
        if split_type == "homology":
            self.splitter = SPLIT_CATALOG[split_type](
                self.dataset.species
            )
        elif split_type == "ss": # only for lncRNA
            self.splitter = SPLIT_CATALOG[split_type](
                self.dataset.data_df.sequence.tolist(),
                ss_map_path = kwargs["ss_map_path"] if "ss_map_path" in kwargs else None,
                threshold = kwargs["threshold"] if "threshold" in kwargs else 0.75,
                dataset_name = self.dataset.dataset_name
            )
        else:
            self.splitter = SPLIT_CATALOG["default"]()

        self.split_ratios = split_ratios
        self.eval_all_splits = eval_all_splits

    def get_output_filename(self, random_seed: str | int) -> str:
        """Generate output filename for linear probing results.

        Args:
            random_seed: Random seed used for data split, or 'all' if getting
                file name for multi-run results.

        Returns:
            Filename for linear probing results.
        """
        out_fn = "result_lp_{}_{}_o{}_{}_tcol-{}_split-{}".format(
            self.dataset.dataset_name,
            self.model_short_name,
            self.seq_chunk_overlap,
            self.task,
            self.target_col,
            self.split_type
        )

        if random_seed == "all":
            out_fn += "_rs-all"
        else:
            out_fn += "_rs-{}".format(random_seed)

        out_fn += ".json"

        return out_fn

    def persist_run_results(
        self,
        metrics: dict[str, float] | dict[str, str],
        random_seed: int | str
    ):
        """Persist linear probe results.

        Args:
            metrics: Linear probing metrics.
            random_seed: Random seed used for data split, or 'all'.
        """
        dataset_root = Path(self.dataset.dataset_path)

        result_dir = dataset_root / "lp_results"
        result_dir.mkdir(exist_ok=True)

        result_fn = self.get_output_filename(random_seed)

        with open(result_dir / result_fn, "w") as f:
            json.dump(metrics, f)

    def concat_embeddings(self, embeddings: np.ndarray):
        """Merge embeddings with benchmark dataframe.

        Assumes that the dataframe rows and embedding order is identical.

        Args:
            embeddings: Embeddings in order of dataset. Shape (N x D).
        """
        self.data_df["embeddings"] = list(embeddings)

    def get_df_splits(
        self,
        random_seed: int,
        dropna: bool = True
    ) -> dict[str, np.ndarray]:
        """Get the train, validation, test data and label splits.

        Args:
            random_seed: Random seed used for generating data splits.
            dropna: Drop rows with NaN values in target column.

        Returns:
            Dictionary containing training, validation, testing splits for
            data and labels as numpy arrays.
        """
        data_df_copy = self.data_df.copy()

        if dropna:
            data_df_copy = data_df_copy.dropna(subset=[self.target_col])

        train_df, val_df, test_df = self.splitter.get_all_splits_df(
            data_df_copy,
            self.split_ratios,
            random_seed
        )

        splits = {
            "train_X": np.array(train_df["embeddings"].tolist()),
            "val_X": np.array(val_df["embeddings"].tolist()),
            "test_X": np.array(test_df["embeddings"].tolist()),
            "train_y": train_df[self.target_col].to_numpy(),
            "val_y": val_df[self.target_col].to_numpy(),
            "test_y": test_df[self.target_col].to_numpy(),
        }

        if isinstance(splits["train_y"][0], np.ndarray):
            splits["train_y"] = np.vstack(list(splits["train_y"]))
            splits["val_y"] = np.vstack(list(splits["val_y"]))
            splits["test_y"] = np.vstack(list(splits["test_y"]))
        else:
            splits["train_y"] = splits["train_y"]
            splits["val_y"] = splits["val_y"]
            splits["test_y"] = splits["test_y"]

        return splits

    def run_linear_probe(
        self,
        random_seed: int = 2541,
        persist: bool = False,
        dropna: bool = True
    ) -> dict[str, float]:
        """Perform data split and run linear probe.

        Args:
            random_seed: Random seed used for data split.
            persist: Save results to data directory.
            dropna: Drop rows with NaN values in target column

        Returns:
            Dictionary of linear probing metrics per split.
        """
        try:
            model = self.linear_models[self.task]
        except KeyError:
            print("Invalid task name.")
            raise

        splits = self.get_df_splits(random_seed, dropna)

        np.random.seed(random_seed)
        model.fit(splits["train_X"], splits["train_y"])

        if self.task in ["regression", "reg_lin", "reg_ridge"]:
            metrics = self.eval_regression(model, splits)
        elif self.task == "classification":
            metrics = self.eval_classification(model, splits)
        elif self.task == "multilabel":
            metrics = self.eval_multilabel(model, splits)

        if persist:
            self.persist_run_results(metrics, random_seed)

        return metrics

    def eval_regression(
        self,
        model: RegressorMixin,
        splits: dict[str, np.ndarray]
    ) -> dict[str, float]:
        """Perform linear probing on regression task.

        Args:
            model: Scikit-learn regression model.
            splits: Data splits used for linear probing.

        Returns:
            Dictionary of linear probing metrics per split.
        """
        outputs = {"val": model.predict(splits["val_X"])}
        if self.eval_all_splits:
            outputs["train"] = model.predict(splits["train_X"])
            outputs["test"] = model.predict(splits["test_X"])

        metrics = {}

        for s_name, split_pred in outputs.items():
            split_y = splits[s_name + "_y"]
            metrics[s_name + "_mse"] = np.mean((split_pred - split_y) ** 2)
            metrics[s_name + "_r"] = pearsonr(split_pred, split_y).statistic
            metrics[s_name + "_p"] = spearmanr(split_pred, split_y).statistic

        return metrics

    def eval_classification(
        self,
        model: ClassifierMixin,
        splits: dict[str, np.ndarray]
    ) -> dict[str, float]:
        """Perform linear probing on classification task.

        Args:
            model: Scikit-learn classification model.
            splits: Data splits used for linear probing.

        Returns:
            Dictionary of linear probing metrics per split.
        """
        outputs = {"val": model.predict_proba(splits["val_X"])[:, 1]}
        if self.eval_all_splits:
            outputs["train"] = model.predict_proba(splits["train_X"])[:, 1]
            outputs["test"] = model.predict_proba(splits["test_X"])[:, 1]

        metrics = {}

        for s_name, split_pred in outputs.items():
            split_y = splits[s_name + "_y"]
            metrics[s_name + "_auroc"] = roc_auc_score(split_y, split_pred)
            metrics[s_name + "_auprc"] = average_precision_score(
                split_y,
                split_pred
            )

        return metrics

    def eval_multilabel(
        self,
        model: MultiOutputClassifier,
        splits: dict[str, np.ndarray]
    ) -> dict[str, float]:
        """Perform linear probing on multilabel classification task.

        Args:
            model: Scikit-learn classification model supporting multi-output.
            splits: Data splits used for linear probing.

        Returns:
            Dictionary of linear probing metrics per split.
        """
        outputs = {"val": model.predict_proba(splits["val_X"])}
        if self.eval_all_splits:
            outputs["train"] = model.predict_proba(splits["train_X"])
            outputs["test"] = model.predict_proba(splits["test_X"])

        metrics = {}

        for s_name, split_pred in outputs.items():
            split_pred = np.swapaxes(np.array(split_pred), 0, 1)[:, :, 1]

            split_y = splits[s_name + "_y"]
            metrics[s_name + "_auroc"] = roc_auc_score(
                split_y,
                split_pred,
                average="micro"
            )
            metrics[s_name + "_auprc"] = average_precision_score(
                split_y,
                split_pred,
                average="micro"
            )

        return metrics

    def linear_probe_multirun(
        self,
        random_seeds: list[int],
        persist: bool = False
    ) -> dict[int, dict[str, float]]:
        """Run multiple linear probes with distinct data split randomization.

        Args:
            random_seeds: Trandom seeds used per individual linear probe run.
            persist: Save results to data directory.

        Returns:
            Dictionary of metrics per random seed used to generate data splits
            for each individual linear probing run.
        """
        metrics = {}
        for random_seed in random_seeds:
            metric = self.run_linear_probe(random_seed, persist)
            metrics[random_seed] = metric
        return metrics

    def load_results(
        self,
        random_seeds: list[int]
    ) -> dict[int, dict[str, float]]:
        """Load multi-run linear probing results from persisted files.

        Args:
            random_seeds: Random seeds used for data splits.

        Returns:
            Dictionary of metrics per random seed used to generate data splits
            for each individual linear probing run.
        """
        metrics = {}
        dataset_root = Path(self.dataset.dataset_path)

        result_dir = dataset_root / "lp_results"

        for random_seed in random_seeds:
            result_fn = self.get_output_filename(random_seed)

            with open(result_dir / result_fn, "r") as f:
                metrics[random_seed] = json.load(f)

        return metrics

    def compute_multirun_results(
        self,
        metrics: dict[int, dict[str, float]],
        print_output: bool = False,
        ci_multiplier: float = 1.96,
        persist: bool = False
    ) -> dict[str, str]:
        """Aggregate multi-run linear probing results.

        Prints mean metric and confidence interval at desired level.

        Args:
            metrics: Result of multi-run linear probing.
            print_output: Prints aggregated metrics.
            ci_multiplier: Constant multiplied to standard error to get CI.
            persist: Save results to data directory.

        Returns:
            Dictionary of mean metric and CI per data split.
        """
        metric_vals: dict[str, list[float]] = {}

        for metric_dict in metrics.values():
            for metric_name, metric_val in metric_dict.items():
                metric_vals.setdefault(metric_name, []).append(metric_val)

        metric_mean = {k: np.mean(v) for k, v in metric_vals.items()}
        metric_std = {k: np.std(v) for k, v in metric_vals.items()}

        metric_out = {}

        for k in metric_vals.keys():
            se = ci_multiplier * (metric_std[k] / (np.sqrt(len(metrics))))
            metric_out[k] = "{} ± {}".format(metric_mean[k], se)

            if print_output:
                print("{} ± {}".format(metric_mean[k], se))

        if persist:
            self.persist_run_results(metric_out, "all")

        return metric_out
