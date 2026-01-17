"""Embedding type definitions for section-level semantic matching (Story 7.11)."""

from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np
from numpy.typing import NDArray

WorkUnitSection = Literal["title", "problem", "actions", "outcome", "skills"]
JDSection = Literal["requirements", "skills", "full"]


class WorkUnitSectionEmbeddings(TypedDict, total=False):
    """Embeddings for each work unit section.

    Keys correspond to WorkUnitSection literals.
    Each value is a numpy float32 array of shape (embedding_dim,).
    """

    title: NDArray[np.float32]
    problem: NDArray[np.float32]
    actions: NDArray[np.float32]
    outcome: NDArray[np.float32]
    skills: NDArray[np.float32]


class JDSectionEmbeddings(TypedDict, total=False):
    """Embeddings for each job description section.

    Keys correspond to JDSection literals.
    Each value is a numpy float32 array of shape (embedding_dim,).
    """

    requirements: NDArray[np.float32]
    skills: NDArray[np.float32]
    full: NDArray[np.float32]
