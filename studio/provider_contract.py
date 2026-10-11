"""Provider-portable contracts; intentionally no installed inference adapter.

Provenance: ChatGPT GPT-6, EX-0001.
"""
from dataclasses import dataclass
from typing import Protocol, Literal


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationRequest:
    shot_id: str
    prompt: str
    reference_asset_ids: tuple[str, ...]
    frame_count: int
    fps: int
    mode: Literal["text_to_video", "image_to_video", "video_to_video", "motion_transfer"]


@dataclass(frozen=True)
class GenerationReceipt:
    shot_id: str
    provider_id: str
    artifact_sha256: str
    duration_frames: int
    provenance_id: str
    review_status: Literal["unreviewed", "accepted", "rejected"] = "unreviewed"


class MediaProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationReceipt:
        """Return truthful provider evidence for one independently verified clip."""


class DisabledProvider:
    """Safe default: no Excelnt, Mage, Drive, cloud GPU or paid model traffic."""

    def generate(self, request: GenerationRequest) -> GenerationReceipt:
        raise ProviderUnavailable(
            "No reviewed cloud provider enabled; plans are not rendered assets"
        )
