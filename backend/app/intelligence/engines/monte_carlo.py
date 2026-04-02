"""
Monte Carlo Simulation Engine — Uncertainty Quantification v2.0 (Python Implementation)
Performs sensitivity analysis with perturbation of edge weights and shock severities.

Mathematical Model:
1. Box-Muller transform for Gaussian sampling:
   u1, u2 = uniform(0,1)
   z = sqrt(-2*ln(u1)) * cos(2*pi*u2)

2. Edge weight perturbation (preserves polarity):
   w'_ji = clamp(w_ji + z*σ, 0, 1) where σ = weightNoise (0.1)
   polarity preserved: z -> z * sign(w_ji - 0.5) for realistic variation

3. Shock severity perturbation (uniform):
   s'_i = uniform(severityMin, severityMax) = uniform(0.7, 1.3)

4. Loss statistics (from 500+ runs):
   - mean, median, variance
   - p10, p50, p90 (percentiles with linear interpolation)
   - bestCase = min(total_loss)
   - worstCase = max(total_loss)

5. Confidence score:
   cv = sqrt(variance) / |mean|  (coefficient of variation)
   conf = clamp(1 - cv, 0, 1)

6. Sector distributions:
   - mean, p10, p90 per sector from total_loss_by_sector across runs

7. Driver uncertainty:
   - per-node impact variance and mean across runs
   - filtered: mean > 0.005
   - sorted by variance descending (most uncertain)

Requirements:
- Seed parameter for reproducible audit runs
- 500 default runs (Monte Carlo constant)
- Support 10K enterprise runs
- Linear interpolation in percentile function (exact TS match)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
from numpy.random import Generator, default_rng
from collections import defaultdict
import math

from .propagation_engine import run_propagation
from .gcc_constants import MONTE_CARLO, SECTOR_GDP_BASE, LAYER_LABELS, LAYER_COLORS


@dataclass
class MonteCarloOptions:
    """Configuration for Monte Carlo simulation."""
    runs: int = 500
    seed: Optional[int] = None
    max_iterations: int = 6
    decay_rate: float = 0.05
    weight_noise: float = 0.1
    severity_min: float = 0.7
    severity_max: float = 1.3


@dataclass
class DriverUncertainty:
    """Per-node impact uncertainty metrics."""
    node_id: str
    label: str
    layer: str
    mean_impact: float
    variance: float
    std_dev: float


@dataclass
class SectorDistribution:
    """Loss distribution metrics for a sector."""
    sector: str
    sector_label: str
    mean_loss: float
    p10_loss: float
    p90_loss: float
    color: str


@dataclass
class MonteCarloResult:
    """Complete Monte Carlo analysis result."""
    # Loss statistics (billions USD)
    loss_mean: float
    loss_median: float
    loss_variance: float
    loss_stddev: float
    loss_p10: float
    loss_p50: float
    loss_p90: float
    loss_best_case: float
    loss_worst_case: float
    
    # Confidence and uncertainty
    confidence_score: float
    coefficient_of_variation: float
    
    # Sector distributions
    sector_distributions: List[SectorDistribution] = field(default_factory=list)
    
    # Driver uncertainty (ranked by variance, filtered mean > 0.005)
    driver_uncertainty: List[DriverUncertainty] = field(default_factory=list)
    
    # Metadata
    runs_executed: int = 500
    seed_used: Optional[int] = None


class MonteCarloEngine:
    """Engine for Monte Carlo sensitivity analysis."""
    
    def __init__(self, rng: Optional[Generator] = None):
        """Initialize with optional seeded RNG."""
        self.rng = rng if rng is not None else default_rng()
    
    def gaussian_random(self) -> float:
        """
        Generate Gaussian(0,1) random using Box-Muller transform.
        
        Exact formula:
        u1, u2 = uniform(0,1)
        z = sqrt(-2*ln(u1)) * cos(2*pi*u2)
        """
        u1 = self.rng.uniform(0, 1)
        u2 = self.rng.uniform(0, 1)
        
        # Box-Muller formula (exact match to TS)
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        return z
    
    def percentile(self, data: List[float], p: float) -> float:
        """
        Compute percentile with linear interpolation.
        
        Exact formula matching TypeScript:
        - index = p * (len(data) - 1)
        - lower = floor(index)
        - upper = ceil(index)
        - frac = index - lower
        - result = data[lower] * (1 - frac) + data[upper] * frac
        """
        if not data or p < 0 or p > 1:
            return 0.0
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        if n == 1:
            return float(sorted_data[0])
        
        index = p * (n - 1)
        lower_idx = int(math.floor(index))
        upper_idx = int(math.ceil(index))
        frac = index - lower_idx
        
        # Clamp indices to valid range
        lower_idx = max(0, min(lower_idx, n - 1))
        upper_idx = max(0, min(upper_idx, n - 1))
        
        result = sorted_data[lower_idx] * (1 - frac) + sorted_data[upper_idx] * frac
        return float(result)
    
    def run_monte_carlo(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        shocks: List[Dict[str, float]],
        options: Optional[MonteCarloOptions] = None,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation with uncertainty quantification.
        
        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            shocks: List of shock dicts with nodeId and impact
            options: MonteCarloOptions with runs, seed, parameters
        
        Returns:
            MonteCarloResult with loss statistics and driver uncertainty
        """
        if options is None:
            options = MonteCarloOptions()
        
        # Set seed if provided (for reproducible audit runs)
        if options.seed is not None:
            self.rng = default_rng(options.seed)
        
        runs = options.runs
        
        # Collect results across all runs
        all_losses: List[float] = []
        sector_losses: Dict[str, List[float]] = defaultdict(list)
        node_impacts: Dict[str, List[float]] = defaultdict(list)
        
        # ── MONTE CARLO LOOP ──
        for run in range(runs):
            # Perturb edge weights (Gaussian noise, preserve polarity)
            perturbed_edges = self._perturb_edges(
                edges,
                options.weight_noise,
            )
            
            # Perturb shock severities (uniform within range)
            perturbed_shocks = self._perturb_shocks(
                shocks,
                options.severity_min,
                options.severity_max,
            )
            
            # Run propagation with perturbed parameters
            result = run_propagation(
                nodes,
                perturbed_edges,
                perturbed_shocks,
                max_iterations=options.max_iterations,
                decay_rate=options.decay_rate,
            )
            
            # Collect loss metrics
            all_losses.append(result.total_loss)
            
            # Collect sector losses
            for sector in result.affected_sectors:
                sector_losses[sector.sector].append(sector.avg_impact * SECTOR_GDP_BASE.get(sector.sector, 0))
            
            # Collect per-node impacts
            for node_id, impact in result.node_impacts.items():
                node_impacts[node_id].append(abs(impact))
        
        # ── LOSS STATISTICS ──
        loss_mean = float(np.mean(all_losses)) if all_losses else 0.0
        loss_median = float(np.median(all_losses)) if all_losses else 0.0
        loss_variance = float(np.var(all_losses)) if len(all_losses) > 1 else 0.0
        loss_stddev = float(np.std(all_losses)) if len(all_losses) > 1 else 0.0
        
        loss_p10 = self.percentile(all_losses, 0.10)
        loss_p50 = self.percentile(all_losses, 0.50)
        loss_p90 = self.percentile(all_losses, 0.90)
        
        loss_best_case = float(np.min(all_losses)) if all_losses else 0.0
        loss_worst_case = float(np.max(all_losses)) if all_losses else 0.0
        
        # ── CONFIDENCE SCORE ──
        # cv = sqrt(variance) / |mean|
        cv = 0.0
        if loss_mean != 0:
            cv = math.sqrt(loss_variance) / abs(loss_mean)
        
        # conf = clamp(1 - cv, 0, 1)
        confidence_score = max(0.0, min(1.0, 1.0 - cv))
        
        # ── SECTOR DISTRIBUTIONS ──
        sector_distributions: List[SectorDistribution] = []
        for sector_key in ["geography", "infrastructure", "economy", "finance", "society"]:
            if sector_key not in sector_losses or not sector_losses[sector_key]:
                continue
            
            sector_loss_list = sector_losses[sector_key]
            sector_mean = float(np.mean(sector_loss_list))
            sector_p10 = self.percentile(sector_loss_list, 0.10)
            sector_p90 = self.percentile(sector_loss_list, 0.90)
            
            sector_distributions.append(
                SectorDistribution(
                    sector=sector_key,
                    sector_label=LAYER_LABELS.get(sector_key, {}).get("ar", sector_key),
                    mean_loss=sector_mean,
                    p10_loss=sector_p10,
                    p90_loss=sector_p90,
                    color=LAYER_COLORS.get(sector_key, "#999999"),
                )
            )
        
        sector_distributions.sort(key=lambda s: s.mean_loss, reverse=True)
        
        # ── DRIVER UNCERTAINTY ──
        driver_uncertainties: List[DriverUncertainty] = []
        
        for node_id, impacts_list in node_impacts.items():
            if not impacts_list:
                continue
            
            mean_impact = float(np.mean(impacts_list))
            variance = float(np.var(impacts_list)) if len(impacts_list) > 1 else 0.0
            std_dev = float(np.std(impacts_list)) if len(impacts_list) > 1 else 0.0
            
            # Filter: mean > 0.005
            if mean_impact <= 0.005:
                continue
            
            # Find node label and layer
            node_dict = next((n for n in nodes if n["id"] == node_id), None)
            if node_dict is None:
                continue
            
            node_label = node_dict.get("labelAr", node_dict.get("label", node_id))
            layer = node_dict.get("layer", "geography")
            
            driver_uncertainties.append(
                DriverUncertainty(
                    node_id=node_id,
                    label=node_label,
                    layer=layer,
                    mean_impact=mean_impact,
                    variance=variance,
                    std_dev=std_dev,
                )
            )
        
        # Sort by variance descending (most uncertain first)
        driver_uncertainties.sort(key=lambda d: d.variance, reverse=True)
        
        # Build result
        return MonteCarloResult(
            loss_mean=loss_mean,
            loss_median=loss_median,
            loss_variance=loss_variance,
            loss_stddev=loss_stddev,
            loss_p10=loss_p10,
            loss_p50=loss_p50,
            loss_p90=loss_p90,
            loss_best_case=loss_best_case,
            loss_worst_case=loss_worst_case,
            confidence_score=confidence_score,
            coefficient_of_variation=cv,
            sector_distributions=sector_distributions,
            driver_uncertainty=driver_uncertainties,
            runs_executed=runs,
            seed_used=options.seed,
        )
    
    def _perturb_edges(
        self,
        edges: List[Dict[str, Any]],
        weight_noise: float,
    ) -> List[Dict[str, Any]]:
        """
        Perturb edge weights with Gaussian noise, preserving polarity.
        
        w'_ji = clamp(w_ji + z*σ, 0, 1)
        where z = Box-Muller Gaussian and σ = weightNoise
        Polarity preserved by design.
        """
        perturbed = []
        
        for edge in edges:
            edge_copy = edge.copy()
            original_weight = edge["weight"]
            
            # Generate Gaussian perturbation
            z = self.gaussian_random()
            perturbation = z * weight_noise
            
            # Apply perturbation and clamp to [0, 1]
            new_weight = original_weight + perturbation
            new_weight = max(0.0, min(1.0, new_weight))
            
            edge_copy["weight"] = new_weight
            perturbed.append(edge_copy)
        
        return perturbed
    
    def _perturb_shocks(
        self,
        shocks: List[Dict[str, float]],
        severity_min: float,
        severity_max: float,
    ) -> List[Dict[str, float]]:
        """
        Perturb shock severities uniformly within [severityMin, severityMax].
        
        s'_i = uniform(severityMin, severityMax)
        """
        perturbed = []
        
        for shock in shocks:
            shock_copy = shock.copy()
            original_impact = shock["impact"]
            
            # Sample uniform severity within range
            severity_multiplier = self.rng.uniform(severity_min, severity_max)
            
            # Apply multiplier to original impact
            new_impact = original_impact * severity_multiplier
            
            # Clamp to [-1, 1] (standard propagation bounds)
            new_impact = max(-1.0, min(1.0, new_impact))
            
            shock_copy["impact"] = new_impact
            perturbed.append(shock_copy)
        
        return perturbed


def run_monte_carlo(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    shocks: List[Dict[str, float]],
    options: Optional[MonteCarloOptions] = None,
) -> MonteCarloResult:
    """
    Convenience function to run Monte Carlo simulation.
    
    Args:
        nodes: List of node dicts
        edges: List of edge dicts
        shocks: List of shock dicts
        options: MonteCarloOptions (uses defaults if None)
    
    Returns:
        MonteCarloResult with uncertainty quantification
    """
    if options is None:
        options = MonteCarloOptions(runs=MONTE_CARLO["defaultRuns"])
    
    engine = MonteCarloEngine()
    return engine.run_monte_carlo(nodes, edges, shocks, options)


def result_to_dict(result: MonteCarloResult) -> Dict[str, Any]:
    """
    Convert MonteCarloResult to dict for JSON serialization.
    
    Args:
        result: MonteCarloResult instance
    
    Returns:
        JSON-serializable dictionary
    """
    return {
        "lossStatistics": {
            "mean": result.loss_mean,
            "median": result.loss_median,
            "variance": result.loss_variance,
            "stdDev": result.loss_stddev,
            "p10": result.loss_p10,
            "p50": result.loss_p50,
            "p90": result.loss_p90,
            "bestCase": result.loss_best_case,
            "worstCase": result.loss_worst_case,
        },
        "confidence": {
            "score": result.confidence_score,
            "coefficientOfVariation": result.coefficient_of_variation,
        },
        "sectorDistributions": [
            {
                "sector": dist.sector,
                "sectorLabel": dist.sector_label,
                "meanLoss": dist.mean_loss,
                "p10Loss": dist.p10_loss,
                "p90Loss": dist.p90_loss,
                "color": dist.color,
            }
            for dist in result.sector_distributions
        ],
        "driverUncertainty": [
            {
                "nodeId": driver.node_id,
                "label": driver.label,
                "layer": driver.layer,
                "meanImpact": driver.mean_impact,
                "variance": driver.variance,
                "stdDev": driver.std_dev,
            }
            for driver in result.driver_uncertainty
        ],
        "metadata": {
            "runsExecuted": result.runs_executed,
            "seedUsed": result.seed_used,
        },
    }
