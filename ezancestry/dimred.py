from pathlib import Path

import joblib
import pandas as pd
import umap
from loguru import logger
from sklearn.decomposition import PCA
from sklearn.neighbors import NeighborhoodComponentsAnalysis as nca

from ezancestry.config import models_directory as _models_directory


def dimensionality_reduction(
    df,
    algorithm="pca",
    aisnps_set="kidd",
    n_components=3,
    overwrite_model=False,
    labels=None,
    population_level="superpopulation",
    models_directory=None,
    random_state=None,
):
    """Reduce the dimensionality of the aisnps
    :param df: One-hot encoded aisnps.
    :type df: pandas DataFrame
    :param algorithm: The type of dimensionality reduction to perform.
        One of {pca, umap, t-SNE, nca}
    :type algorithm: str
    :param aisnps_set: One of either {kidd, seldin}
    :type aisnps_set: str
    :param n_components: The number of components to use for dimensionality reduction.
    :param n_components: int
    :param overwrite_model: Whether to overwrite the model.
    :type overwrite_mode: bool
    :param labels: If algorithm is "nca", then labels for the records in the
    DataFrame are used for the dimensionality reduction.
    :type labels: array-like
    :param population_level: Either {"population" or "super population"} If
    algorithm is "nca", then population_level is used to name the
    dimensionality reduction model file.
    :type population_level: str
    :param models_directory: The directory to save the model to.
    :type models_directory: str
    :param random_state: The random_state is used to seed the dimensionality reduction model. If None (default), then a random seed is chosen.
    :type random_state: int or None
    :returns: The transformed X DataFrame, reduced to 3 components by <algorithm>.
    """
    algorithm = algorithm.lower()
    aisnps_set = aisnps_set.lower()

    if models_directory is None:
        models_directory = _models_directory
    models_directory = Path(models_directory)

    population_level = (
        population_level.replace("-", "").replace(" ", "").lower()
    )
    columns = [
        col
        for col in df.columns
        if col not in ("gender", "population", "superpopulation")
    ]
    df = df[columns]
    if overwrite_model:
        if algorithm in set(["pca", "umap"]):
            if algorithm == "pca":
                reducer = PCA(
                    n_components=n_components, random_state=random_state
                )
            elif algorithm == "umap":
                reducer = umap.UMAP(
                    n_components=n_components,
                    min_dist=0.2,
                    metric="dice",
                    random_state=random_state,
                )
            else:
                pass
            df_reduced = reducer.fit_transform(df.values)
            joblib.dump(
                reducer,
                models_directory.joinpath(f"{algorithm}.{aisnps_set}.bin"),
            )
        elif algorithm == "nca":
            reducer = nca(
                n_components=n_components,
                random_state=random_state,
            )
            df_reduced = reducer.fit_transform(df.values, labels)
            joblib.dump(
                reducer,
                models_directory.joinpath(
                    f"{algorithm}.{aisnps_set}.{population_level}.bin"
                ),
            )
        else:
            return None

        logger.info(
            f"Successfully wrote a dimensionality reduction model to {models_directory}"
        )
    else:
        # load reducer and return reduced X
        if algorithm in set(["pca", "umap"]):
            try:
                reducer = joblib.load(
                    models_directory.joinpath(f"{algorithm}.{aisnps_set}.bin")
                )
            except FileNotFoundError:
                return None
        elif algorithm == "nca":
            try:
                reducer = joblib.load(
                    models_directory.joinpath(
                        f"{algorithm}.{aisnps_set}.{population_level}.bin"
                    )
                )
            except FileNotFoundError:
                return None
        else:
            logger.warning(
                "Could not find a matching dimensionality reduction model on disk for your algorithm type"
            )
        df_reduced = reducer.transform(df.values)
        logger.info("Successfully loaded a dimensionality reduction model")

    return pd.DataFrame(df_reduced, columns=["x", "y", "z"], index=df.index)
