"""Immutable, provider-neutral cinematic episode planning contracts.

Provenance: created by ChatGPT GPT-6 for independent foundation Task EX-0001.
These are INTENT/PLAN records, never evidence that an asset was rendered.
"""
from dataclasses import dataclass
from typing import Optional
import re


class PlanError(ValueError):
    """Plan violates a deterministic acceptance constraint."""


_ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")


def _id(value: str, label: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PlanError(f"Invalid {label}")


@dataclass(frozen=True)
class Character:
    character_id: str
    voice_profile_id: str
    visual_reference_id: str

    def validate(self) -> None:
        _id(self.character_id, "character ID")
        _id(self.voice_profile_id, "voice profile ID")
        _id(self.visual_reference_id, "visual reference ID")


@dataclass(frozen=True)
class Shot:
    shot_id: str
    scene_id: str
    start_frame: int
    frame_count: int
    visible_character_ids: tuple[str, ...] = ()
    dialogue_speaker_id: Optional[str] = None
    reference_asset_ids: tuple[str, ...] = ()
    modality: str = "image_to_video"

    def validate(self) -> None:
        _id(self.shot_id, "shot ID")
        _id(self.scene_id, "scene ID")
        if type(self.start_frame) is not int or self.start_frame < 0:
            raise PlanError("Shot starts at an invalid frame")
        if type(self.frame_count) is not int or self.frame_count <= 0:
            raise PlanError("Shot frame count must be positive")
        if self.modality not in {
            "text_to_video", "image_to_video", "video_to_video", "motion_transfer"
        }:
            raise PlanError("Unknown provider modality")
        if not isinstance(self.visible_character_ids, tuple) or len(set(self.visible_character_ids)) != len(self.visible_character_ids):
            raise PlanError("Duplicate or invalid character list")
        for character_id in self.visible_character_ids:
            _id(character_id, "visible character ID")
        if self.dialogue_speaker_id is not None:
            _id(self.dialogue_speaker_id, "speaker ID")
            if self.dialogue_speaker_id not in self.visible_character_ids:
                raise PlanError("Dialogue speaker must be associated with shot")
        if not isinstance(self.reference_asset_ids, tuple) or len(set(self.reference_asset_ids)) != len(self.reference_asset_ids):
            raise PlanError("Duplicate references")
        for reference_id in self.reference_asset_ids:
            _id(reference_id, "reference asset ID")


@dataclass(frozen=True)
class Scene:
    scene_id: str
    shots: tuple[Shot, ...]
    location_reference_id: str

    def validate(self) -> None:
        _id(self.scene_id, "scene ID")
        _id(self.location_reference_id, "location reference ID")
        if not isinstance(self.shots, tuple) or not self.shots:
            raise PlanError("Every scene must contain shots")
        for shot in self.shots:
            if type(shot) is not Shot:
                raise PlanError("Invalid shot record")
            shot.validate()
            if shot.scene_id != self.scene_id:
                raise PlanError("Shot scene association mismatch")


@dataclass(frozen=True)
class Episode:
    episode_id: str
    scenes: tuple[Scene, ...]
    characters: tuple[Character, ...]
    fps: int = 24
    width: int = 1920
    height: int = 1080
    duration_seconds: int = 1200

    def validate(self) -> None:
        _id(self.episode_id, "episode ID")
        if type(self.fps) is not int or self.fps not in (24, 25, 30, 60):
            raise PlanError("Unsupported frames per second")
        if (type(self.width) is not int or type(self.height) is not int or
                self.width <= 0 or self.height <= 0 or
                self.width * 9 != self.height * 16):
            raise PlanError("Episode must have a 16:9 frame")
        if type(self.duration_seconds) is not int or self.duration_seconds != 1200:
            raise PlanError("Movie Studio episodes must target exactly 20 minutes")
        if not isinstance(self.characters, tuple) or not isinstance(self.scenes, tuple):
            raise PlanError("Episode requires immutable character/scene tuples")
        if not self.characters or not self.scenes:
            raise PlanError("Episode requires characters and scenes")
        characters = set()
        voice_profiles = set()
        reference_by_character = {}
        for char in self.characters:
            if type(char) is not Character:
                raise PlanError("Invalid character record")
            char.validate()
            if char.character_id in characters or char.voice_profile_id in voice_profiles:
                raise PlanError("Duplicate character or shared voice profile ID")
            characters.add(char.character_id)
            voice_profiles.add(char.voice_profile_id)
            reference_by_character[char.character_id] = char.visual_reference_id
        cursor = 0
        seen_shots = set()
        seen_scenes = set()
        for scene in self.scenes:
            if type(scene) is not Scene:
                raise PlanError("Invalid scene record")
            scene.validate()
            if scene.scene_id in seen_scenes:
                raise PlanError("Duplicate scene ID")
            seen_scenes.add(scene.scene_id)
            for shot in scene.shots:
                if shot.shot_id in seen_shots:
                    raise PlanError("Duplicate shot ID")
                seen_shots.add(shot.shot_id)
                if shot.start_frame != cursor:
                    raise PlanError("Timeline has a gap, overlap or out-of-order shot")
                if shot.frame_count > self.fps * 15:
                    raise PlanError("Single shot exceeds 15 second provider clip budget")
                for character_id in shot.visible_character_ids:
                    if character_id not in characters:
                        raise PlanError("Shot references unknown character")
                    if reference_by_character[character_id] not in shot.reference_asset_ids:
                        raise PlanError("Visible character lacks their canonical visual reference")
                cursor += shot.frame_count
        if cursor != self.duration_seconds * self.fps:
            raise PlanError("Episode timeline must fill exactly 20 minutes")

    @property
    def shot_count(self) -> int:
        return sum(len(scene.shots) for scene in self.scenes)

    @property
    def planned_frames(self) -> int:
        return sum(shot.frame_count for scene in self.scenes for shot in scene.shots)
