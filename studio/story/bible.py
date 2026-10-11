"""Immutable Movie Bible and character/reference identity contracts.

Creator: ChatGPT GPT-6 · EX-A-0002 · offline, provider independent.
These are story planning records, NOT licensed/rendered media assets.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from dataclasses import dataclass


class StoryError(ValueError):
    """A story record fails strict continuity/provenance validation."""


_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def identifier(value: object, field: str) -> str:
    if type(value) is not str or not _ID.fullmatch(value):
        raise StoryError(f"Invalid {field}")
    return value


def sha256(value: object, field: str) -> str:
    if type(value) is not str or not _SHA.fullmatch(value):
        raise StoryError(f"Invalid {field} digest")
    return value


def natural(value: object, field: str, *, min_value: int = 1) -> int:
    if type(value) is not int or value < min_value:
        raise StoryError(f"Invalid {field}")
    return value


def prose(value: object, field: str, *, max_len: int = 2000) -> str:
    if type(value) is not str or not value.strip() or len(value) > max_len:
        raise StoryError(f"Invalid {field}")
    if any((ord(c) < 32 and c not in "\n\t") or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise StoryError(f"Unsafe {field}")
    return value


def unique_ids(items: object, field: str) -> None:
    if type(items) is not tuple:
        raise StoryError(f"{field} must be immutable tuple")
    if len(items) != len(set(items)):
        raise StoryError(f"Duplicate {field}")
    for item in items:
        identifier(item, field)


@dataclass(frozen=True)
class AssetReference:
    asset_id: str
    version: int
    checksum_sha256: str

    def validate(self) -> None:
        identifier(self.asset_id, "asset ID")
        natural(self.version, "asset version")
        sha256(self.checksum_sha256, "asset")


@dataclass(frozen=True)
class CharacterProfile:
    character_id: str
    role_id: str
    display_name: str
    voice_id: str
    visual: AssetReference
    costume_id: str
    canonical_prop_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        identifier(self.character_id, "character")
        identifier(self.role_id, "role")
        prose(self.display_name, "character name", max_len=160)
        identifier(self.voice_id, "voice")
        if type(self.visual) is not AssetReference:
            raise StoryError("Character missing visual provenance")
        self.visual.validate()
        identifier(self.costume_id, "costume")
        unique_ids(self.canonical_prop_ids, "character prop IDs")


@dataclass(frozen=True)
class LocationProfile:
    location_id: str
    display_name: str
    visual: AssetReference

    def validate(self) -> None:
        identifier(self.location_id, "location")
        prose(self.display_name, "location name", max_len=160)
        if type(self.visual) is not AssetReference:
            raise StoryError("Location missing visual provenance")
        self.visual.validate()


@dataclass(frozen=True)
class MovieBible:
    bible_id: str
    revision: int
    title: str
    logline: str
    characters: tuple[CharacterProfile, ...]
    locations: tuple[LocationProfile, ...]

    def validate(self) -> None:
        identifier(self.bible_id, "bible")
        natural(self.revision, "bible revision")
        prose(self.title, "title", max_len=250)
        prose(self.logline, "logline")
        if type(self.characters) is not tuple or not self.characters:
            raise StoryError("Bible needs characters")
        if type(self.locations) is not tuple or not self.locations:
            raise StoryError("Bible needs locations")
        for item in self.characters:
            if type(item) is not CharacterProfile:
                raise StoryError("Unexpected character record")
            item.validate()
        for item in self.locations:
            if type(item) is not LocationProfile:
                raise StoryError("Unexpected location record")
            item.validate()
        for label, values in (
            ("character ID", (c.character_id for c in self.characters)),
            ("role ID", (c.role_id for c in self.characters)),
            ("voice ID", (c.voice_id for c in self.characters)),
            ("location ID", (l.location_id for l in self.locations)),
        ):
            seq = tuple(values)
            if len(seq) != len(set(seq)):
                raise StoryError(f"Duplicate {label}")

    def character(self, character_id: str) -> CharacterProfile:
        identifier(character_id, "character")
        self.validate()
        for character in self.characters:
            if character.character_id == character_id:
                return character
        raise StoryError("Unknown character")

    def location(self, location_id: str) -> LocationProfile:
        identifier(location_id, "location")
        self.validate()
        for location in self.locations:
            if location.location_id == location_id:
                return location
        raise StoryError("Unknown location")

    def digest(self) -> str:
        self.validate()
        canonical = json.dumps(dataclasses.asdict(self), ensure_ascii=True, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
