"""
Impact Observatory - Decision Output Layer Module

Provides DecisionOutputGenerator for producing structured, bilingual decision
outputs answering mandatory questions about scenario impacts and recommendations.
"""

from .output import DecisionOutputGenerator, DecisionOutput

__all__ = ["DecisionOutputGenerator", "DecisionOutput"]
