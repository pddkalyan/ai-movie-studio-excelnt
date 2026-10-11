"""Cross-scene continuity and exact 20-minute screenplay-to-shot planning.

Creator: ChatGPT GPT-6 · EX-A-0002. Offline planning, no inference calls.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass

from .bible import (AssetReference, MovieBible, StoryError, identifier, natural,
                    prose, sha256, unique_ids)


@dataclass(frozen=True)
class CharacterAppearance:
    character_id: str
    visual: AssetReference
    costume_id: str
    carried_props: tuple[str, ...] = ()

    def validate(self) -> None:
        identifier(self.character_id, "appearance character")
        if type(self.visual) is not AssetReference:
            raise StoryError("Appearance lacks reference provenance")
        self.visual.validate()
        identifier(self.costume_id, "appearance costume")
        unique_ids(self.carried_props, "carried prop IDs")


@dataclass(frozen=True)
class DialogueLine:
    line_id: str
    speaker_character_id: str
    voice_id: str
    text: str

    def validate(self) -> None:
        identifier(self.line_id, "dialogue line")
        identifier(self.speaker_character_id, "speaker")
        identifier(self.voice_id, "dialogue voice")
        prose(self.text, "dialogue", max_len=5000)


@dataclass(frozen=True)
class StoryShot:
    shot_id: str
    scene_id: str
    start_frame: int
    frame_count: int
    appearances: tuple[CharacterAppearance, ...]
    dialogue: tuple[DialogueLine, ...] = ()
    direction: str = "A measured cinematic composition."

    def validate(self) -> None:
        identifier(self.shot_id, "shot")
        identifier(self.scene_id, "shot scene")
        natural(self.start_frame, "shot start", min_value=0)
        natural(self.frame_count, "shot frames")
        prose(self.direction, "shot direction", max_len=3000)
        if type(self.appearances) is not tuple or type(self.dialogue) is not tuple:
            raise StoryError("Shot records must be immutable tuples")
        for appearance in self.appearances:
            if type(appearance) is not CharacterAppearance:
                raise StoryError("Unexpected appearance type")
            appearance.validate()
        for line in self.dialogue:
            if type(line) is not DialogueLine:
                raise StoryError("Unexpected dialogue type")
            line.validate()
        names = tuple(x.character_id for x in self.appearances)
        if len(names) != len(set(names)):
            raise StoryError("Duplicate on-screen character")
        line_ids = tuple(x.line_id for x in self.dialogue)
        if len(line_ids) != len(set(line_ids)):
            raise StoryError("Duplicate dialogue line ID")


@dataclass(frozen=True)
class StoryScene:
    scene_id: str
    ordinal: int
    location_id: str
    location_visual: AssetReference
    synopsis: str
    shots: tuple[StoryShot, ...]

    def validate(self) -> None:
        identifier(self.scene_id, "scene")
        natural(self.ordinal, "scene order")
        identifier(self.location_id, "scene location")
        if type(self.location_visual) is not AssetReference:
            raise StoryError("Scene has no reference version")
        self.location_visual.validate()
        prose(self.synopsis, "scene synopsis", max_len=2000)
        if type(self.shots) is not tuple or not self.shots:
            raise StoryError("Every scene must include shots")
        for shot in self.shots:
            if type(shot) is not StoryShot:
                raise StoryError("Invalid shot record")
            shot.validate()
            if shot.scene_id != self.scene_id:
                raise StoryError("Shot belongs to wrong scene")


@dataclass(frozen=True)
class StoryPlan:
    plan_id: str
    bible_id: str
    bible_revision: int
    bible_digest_sha256: str
    scenes: tuple[StoryScene, ...]
    fps: int = 24
    width: int = 1920
    height: int = 1080
    duration_seconds: int = 1200

    def validate(self, bible: MovieBible) -> None:
        if type(bible) is not MovieBible:
            raise StoryError("Verified Movie Bible required")
        bible.validate()
        identifier(self.plan_id, "plan")
        if self.bible_id != bible.bible_id:
            raise StoryError("Plan bound to wrong Bible")
        natural(self.bible_revision, "bound Bible revision")
        sha256(self.bible_digest_sha256, "bound Bible")
        if self.bible_revision != bible.revision or self.bible_digest_sha256 != bible.digest():
            raise StoryError("Stale or modified Bible; re-authorize plan")
        if (type(self.fps) is not int or self.fps != 24 or type(self.width) is not int
                or type(self.height) is not int or self.width * 9 != self.height * 16
                or self.width <= 0 or self.height <= 0 or type(self.duration_seconds) is not int
                or self.duration_seconds != 1200):
            raise StoryError("Plan must be exactly 20 minutes, 24fps and 16:9")
        if type(self.scenes) is not tuple or not self.scenes:
            raise StoryError("Missing scenes")
        characters = {char.character_id: char for char in bible.characters}
        locations = {loc.location_id: loc for loc in bible.locations}
        seen_scene_ids: set[str] = set()
        seen_shot_ids: set[str] = set()
        seen_line_ids: set[str] = set()
        cursor = 0
        for ordinal, scene in enumerate(self.scenes, start=1):
            if type(scene) is not StoryScene:
                raise StoryError("Invalid scene")
            scene.validate()
            if scene.ordinal != ordinal or scene.scene_id in seen_scene_ids:
                raise StoryError("Scene order/identity drift")
            seen_scene_ids.add(scene.scene_id)
            loc = locations.get(scene.location_id)
            if loc is None or scene.location_visual != loc.visual:
                raise StoryError("Missing, wrong or outdated location reference")
            for shot in scene.shots:
                if shot.shot_id in seen_shot_ids:
                    raise StoryError("Duplicate shot across scenes")
                seen_shot_ids.add(shot.shot_id)
                if shot.start_frame != cursor:
                    raise StoryError("Timeline gap, overlap or out-of-order shot")
                if shot.frame_count > 15 * self.fps:
                    raise StoryError("Shot exceeds 15-second provider budget")
                visible = {a.character_id: a for a in shot.appearances}
                for appearance in shot.appearances:
                    canonical = characters.get(appearance.character_id)
                    if canonical is None:
                        raise StoryError("Unknown on-screen character")
                    if appearance.visual != canonical.visual:
                        raise StoryError("Character reference version/digest mismatch")
                    if appearance.costume_id != canonical.costume_id:
                        raise StoryError("Unapproved costume drift")
                    if not set(appearance.carried_props).issubset(canonical.canonical_prop_ids):
                        raise StoryError("Unapproved prop drift")
                for dialogue in shot.dialogue:
                    if dialogue.line_id in seen_line_ids:
                        raise StoryError("Dialogue line reused across shots")
                    seen_line_ids.add(dialogue.line_id)
                    canonical = characters.get(dialogue.speaker_character_id)
                    if canonical is None or dialogue.speaker_character_id not in visible:
                        raise StoryError("Dialogue speaker not in scene shot")
                    if dialogue.voice_id != canonical.voice_id:
                        raise StoryError("Dialogue voice identity drift")
                cursor += shot.frame_count
        if cursor != self.duration_seconds * self.fps:
            raise StoryError("Timeline does not cover exactly 20 minutes")

    def digest(self, bible: MovieBible) -> str:
        self.validate(bible)
        canonical = json.dumps(dataclasses.asdict(self), ensure_ascii=True, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def example_story_plan(bible: MovieBible) -> StoryPlan:
    """Create a PLAN-only 120-shot continuity fixture; no media provider calls."""
    bible.validate()
    cast = tuple(CharacterAppearance(c.character_id, c.visual, c.costume_id, c.canonical_prop_ids)
                 for c in bible.characters)
    scenes = []
    for n in range(12):
        loc = bible.locations[n % len(bible.locations)]
        scene_id = f"scene_{n + 1:02d}"
        shots = []
        for m in range(10):
            char = bible.characters[(n * 10 + m) % len(bible.characters)]
            line = DialogueLine(f"line_{n + 1:02d}_{m + 1:02d}", char.character_id, char.voice_id,
                                f"Scene {n + 1}, take {m + 1}: the mystery deepens.")
            shots.append(StoryShot(f"shot_{n + 1:02d}_{m + 1:02d}", scene_id,
                                   (n * 10 + m) * 240, 240, cast, (line,)))
        scenes.append(StoryScene(scene_id, n + 1, loc.location_id, loc.visual,
                                 f"The characters explore mystery {n + 1}.", tuple(shots)))
    plan = StoryPlan("episode_plan_001", bible.bible_id, bible.revision, bible.digest(), tuple(scenes))
    plan.validate(bible)
    return plan
