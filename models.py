from dataclasses import dataclass


@dataclass
class AppConfig:
    """Basic configuration values for the app."""
    app_title: str = "Paradox / Polarity Map Generator"


@dataclass
class AnalysisResult:
    """Represents the current output of an analysis step."""
    success: bool
    message: str