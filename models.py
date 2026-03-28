from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Represents the current output of an analysis step."""
    success: bool
    message: str