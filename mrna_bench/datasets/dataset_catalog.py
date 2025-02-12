from collections.abc import Callable

from .benchmark_dataset import BenchmarkDataset
from .go_mol_func import GOMolecularFunction
from .pcg_essentiality import PCGEssentiality
from .lncrna_essentiality import LNCRNAEssentiality
from .rna_hl_human import RNAHalfLifeHuman
from .rna_hl_mouse import RNAHalfLifeMouse
from .prot_loc import ProteinLocalization
from .mrl_sugimoto import MRLSugimoto
from .mrl_sample import (
    MRLSampleEGFP,
    MRLSampleMCherry,
    MRLSampleDesigned,
    MRLSampleVarying
)

DATASET_CATALOG: dict[str, Callable[..., BenchmarkDataset]] = {
    "go-mf": GOMolecularFunction,
    "pcg-ess": PCGEssentiality,
    "lncrna-ess": LNCRNAEssentiality,
    "rnahl-human": RNAHalfLifeHuman,
    "rnahl-mouse": RNAHalfLifeMouse,
    "prot-loc": ProteinLocalization,
    "mrl-sugimoto": MRLSugimoto,
    "mrl-sample-egfp": MRLSampleEGFP,
    "mrl-sample-mcherry": MRLSampleMCherry,
    "mrl-sample-designed": MRLSampleDesigned,
    "mrl-sample-varying": MRLSampleVarying,
}

DATASET_DEFAULT_TASK: dict[str, str] = {
    "go-mf": "multilabel",
    "rnahl-human": "reg_ridge",
    "rnahl-mouse": "reg_ridge",
    "prot-loc": "multilabel",
    "mrl-sugimoto": "reg_ridge",
    "pcg-ess": "classification",
    "lncrna-ess": "classification",
}
