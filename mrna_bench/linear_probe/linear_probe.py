import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from sklearn.base import RegressorMixin, ClassifierMixin
from sklearn.linear_model import RidgeCV, LinearRegression, LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from mrna_bench import load_dataset
from mrna_bench.data_splitter.data_splitter import DataSplitter
from mrna_bench.data_splitter.split_catalog import SPLIT_CATALOG
from mrna_bench.datasets import BenchmarkDataset
from mrna_bench.models import EmbeddingModel, MODEL_CATALOG
from mrna_bench.embedder import get_output_filename


class LinearProbe:
    """Linear Probe Evaluation Module."""

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
        """Load embeddings from persisted location."""
        embeddings_fn = get_output_filename(
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
        split_ratios: tuple[float, float, float] = [0.7, 0.15, 0.15],
        eval_all_splits: bool = False
    ) -> "LinearProbe":
        """Initialize LinearProbe from instantiated dataset and model."""
        embeddings = cls.load_persisted_embeddings(
            dataset.embedding_dir,
            model.short_name,
            dataset.dataset_name,
            seq_chunk_overlap
        )
        return cls(
            dataset,
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
        split_ratios: tuple[float, float, float] = [0.7, 0.15, 0.15],
        eval_all_splits: bool = False
    ) -> "LinearProbe":
        """Initialize LinearProbe using model and dataset names."""
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
        embeddings: np.ndarray,
        task: str,
        target_col: str,
        split_type: str = "homology",
        split_ratios: tuple[float, float, float] = [0.7, 0.15, 0.15],
        eval_all_splits: bool = False
    ):
        self.dataset = dataset
        self.data_df = dataset.data_df

        self.task = task
        self.target_col = target_col

        self.concat_embeddings(embeddings)

        self.splitter: DataSplitter

        if split_type == "homology":
            self.splitter = SPLIT_CATALOG[split_type](
                self.dataset.species
            )
        else:
            self.splitter = SPLIT_CATALOG["default"]

        self.split_ratios = split_ratios
        self.eval_all_splits = eval_all_splits

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
    ) -> dict[str, pd.DataFrame]:
        train_df, val_df, test_df = self.splitter.get_all_splits_df(
            self.data_df,
            self.split_ratios,
            random_seed
        )

        splits = {
            "train_X": np.vstack(train_df["embeddings"]),
            "val_X": np.vstack(val_df["embeddings"]),
            "test_X": np.vstack(test_df["embeddings"]),
            "train_y": train_df[self.target_col],
            "val_y": val_df[self.target_col],
            "test_y": test_df[self.target_col],
        }

        if self.task == "multilabel":
            splits["train_y"] = np.vstack(splits["train_y"])
            splits["val_y"] = np.vstack(splits["val_y"])
            splits["test_y"] = np.vstack(splits["test_y"])

        return splits

    def run_linear_probe(self, random_seed: int = 2541) -> dict[str, float]:
        try:
            model = self.linear_models[self.task]
        except KeyError:
            print("Invalid task name.")
            raise

        splits = self.get_df_splits(random_seed)

        np.random.seed(random_seed)
        model.fit(splits["train_X"], splits["train_y"])

        if self.task in ["regression", "reg_lin", "reg_ridge"]:
            metrics = self.eval_regression(model, splits)
        elif self.task == "classification":
            metrics = self.eval_classification(model, splits)
        elif self.task == "multilabel":
            metrics = self.eval_multilabel(model, splits)

        return metrics

    def eval_regression(
        self,
        model: RegressorMixin,
        splits: dict[str, np.ndarray]
    ) -> dict[str, float]:
        outputs = {"val": model.predict(splits["val_X"])}
        if self.eval_all_splits:
            outputs["train"] = model.predict(splits["train_X"])
            outputs["test"] = model.predict(splits["test_X"])

        metrics = {}

        for s_name, split_pred in outputs.items():
            split_y = splits[s_name + "_y"]
            metrics[s_name + "_mse"] = np.mean((split_pred - split_y) ** 2)
            metrics[s_name + "_r"] = pearsonr(split_pred, split_y).statistic

        return metrics

    def eval_classification(
        self,
        model: ClassifierMixin,
        splits: dict[str, np.ndarray]
    ) -> dict[str, float]:
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
    ) -> dict[int, dict[str, float]]:
        metrics = {}
        for random_seed in random_seeds:
            metric = self.run_linear_probe(random_seed)
            metrics[random_seed] = metric
        return metrics

    def compute_multirun_results(
        self,
        metrics: dict[int, dict[str, float]],
        print_output: bool = False,
        ci_multiplier: float = 1.96
    ) -> dict[str, str]:
        metric_vals = {}

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

        return metric_out
