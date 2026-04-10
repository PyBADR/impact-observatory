"""Boundary constraints — national borders, restricted airspace, straits, geopolitical blocs.

Boundaries act as filters on propagation and diffusion:
- Reflective: energy bounces back (closed border)
- Absorptive: energy is reduced (partial barrier)
- Permeable: energy passes with attenuation (open border with friction)

Each boundary has a permeability coefficient in [0, 1]:
    0 = fully reflective (hard wall)
    1 = fully permeable (no barrier)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray


class BoundaryType(StrEnum):
    NATIONAL_BORDER = "national_border"
    MARITIME_LIMIT = "maritime_limit"
    AIRSPACE_BOUNDARY = "airspace_boundary"
    RESTRICTED_ZONE = "restricted_zone"
    GEOPOLITICAL_BLOC = "geopolitical_bloc"
    CHOKEPOINT = "chokepoint"


@dataclass
class BoundaryConstraint:
    """A single boundary between two nodes or regions."""

    boundary_id: str
    boundary_type: BoundaryType
    node_a: str
    node_b: str
    permeability: float = 0.5  # 0=blocked, 1=open
    description: str = ""


@dataclass
class BoundarySystem:
    """Collection of boundary constraints that modify propagation/diffusion."""

    constraints: list[BoundaryConstraint] = field(default_factory=list)

    def add(
        self,
        boundary_id: str,
        boundary_type: BoundaryType,
        node_a: str,
        node_b: str,
        permeability: float = 0.5,
        description: str = "",
    ) -> None:
        self.constraints.append(
            BoundaryConstraint(
                boundary_id=boundary_id,
                boundary_type=boundary_type,
                node_a=node_a,
                node_b=node_b,
                permeability=permeability,
                description=description,
            )
        )

    def apply_to_adjacency(
        self,
        adjacency: NDArray[np.float64],
        node_ids: list[str],
    ) -> NDArray[np.float64]:
        """Apply boundary constraints to an adjacency matrix.

        Modifies edge weights based on permeability:
            A'_ij = A_ij * permeability(i, j)

        Returns a new modified adjacency matrix.
        """
        idx = {nid: i for i, nid in enumerate(node_ids)}
        modified = adjacency.copy()

        for bc in self.constraints:
            i = idx.get(bc.node_a)
            j = idx.get(bc.node_b)
            if i is not None and j is not None:
                modified[i, j] *= bc.permeability
                modified[j, i] *= bc.permeability  # symmetric for diffusion

        return modified

    def get_boundary_mask(
        self,
        node_ids: list[str],
        blocked_threshold: float = 0.1,
    ) -> NDArray[np.bool_]:
        """Generate a boolean mask of boundary-adjacent nodes.

        A node is flagged if any of its boundary connections have
        permeability below the threshold (effectively blocked).
        """
        mask = np.zeros(len(node_ids), dtype=np.bool_)
        idx = {nid: i for i, nid in enumerate(node_ids)}

        for bc in self.constraints:
            if bc.permeability < blocked_threshold:
                for nid in (bc.node_a, bc.node_b):
                    if nid in idx:
                        mask[idx[nid]] = True
        return mask

    def explain(self) -> list[dict]:
        """Return human-readable boundary constraint descriptions."""
        return [
            {
                "id": bc.boundary_id,
                "type": bc.boundary_type,
                "between": f"{bc.node_a} <-> {bc.node_b}",
                "permeability": bc.permeability,
                "status": "open" if bc.permeability > 0.7 else "restricted" if bc.permeability > 0.2 else "blocked",
                "description": bc.description,
            }
            for bc in self.constraints
        ]


# Pre-defined GCC boundary constraints
GCC_BOUNDARIES = BoundarySystem()
GCC_BOUNDARIES.add("b-hormuz", BoundaryType.CHOKEPOINT, "hormuz", "shipping", 0.9, "Strait of Hormuz chokepoint")
GCC_BOUNDARIES.add("b-iran-gulf", BoundaryType.MARITIME_LIMIT, "hormuz", "oil_sector", 0.7, "Iran-Gulf maritime boundary")
GCC_BOUNDARIES.add("b-gcc-airspace", BoundaryType.AIRSPACE_BOUNDARY, "airspace", "aviation", 0.95, "GCC unified airspace")
GCC_BOUNDARIES.add("b-saudi-yemen", BoundaryType.NATIONAL_BORDER, "saudi", "stability", 0.4, "Saudi-Yemen border zone — conflict spillover risk")
GCC_BOUNDARIES.add("b-kuwait-iraq", BoundaryType.NATIONAL_BORDER, "kuwait", "stability", 0.5, "Kuwait-Iraq border — security sensitivity")
GCC_BOUNDARIES.add("b-qatar-bloc", BoundaryType.GEOPOLITICAL_BLOC, "qatar", "saudi", 0.6, "GCC diplomatic alignment")
