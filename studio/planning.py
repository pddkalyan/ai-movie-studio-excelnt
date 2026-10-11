"""Deterministic proof-of-structure episode; never a generated film.

Provenance: ChatGPT GPT-6, EX-0001. All references are fictional placeholders.
"""
from .contracts import Character, Episode, Scene, Shot


def build_example_episode() -> Episode:
    """12 scenes x 10 shots x 10 seconds = exactly 20 minutes, 16:9, 24 fps."""
    characters = (
        Character("hero", "voice_hero_v1", "reference_hero_v1"),
        Character("partner", "voice_partner_v1", "reference_partner_v1"),
    )
    frames_per_shot = 10 * 24
    scene_plans = []
    for scene_num in range(1, 13):
        scene_id = f"scene_{scene_num:02d}"
        shots = []
        for shot_num in range(1, 11):
            shot_id = f"shot_{scene_num:02d}_{shot_num:02d}"
            speaker = "hero" if shot_num % 2 else "partner"
            shots.append(Shot(
                shot_id=shot_id,
                scene_id=scene_id,
                start_frame=((scene_num - 1) * 10 + shot_num - 1) * frames_per_shot,
                frame_count=frames_per_shot,
                visible_character_ids=("hero", "partner"),
                dialogue_speaker_id=speaker,
                reference_asset_ids=("reference_hero_v1", "reference_partner_v1"),
                modality="image_to_video",
            ))
        scene_plans.append(Scene(
            scene_id=scene_id,
            shots=tuple(shots),
            location_reference_id=f"location_{scene_num:02d}",
        ))
    plan = Episode(
        episode_id="demo_episode_001",
        scenes=tuple(scene_plans),
        characters=characters,
    )
    plan.validate()
    return plan


def summarize_plan(plan: Episode) -> dict:
    plan.validate()
    return {
        "episode_id": plan.episode_id,
        "duration_seconds": plan.duration_seconds,
        "fps": plan.fps,
        "resolution": f"{plan.width}x{plan.height}",
        "aspect_ratio": "16:9",
        "total_frames": plan.planned_frames,
        "scenes": len(plan.scenes),
        "shots": plan.shot_count,
        "plan_only": True,
        "rendered_clips": 0,
        "verified_audio": False,
        "archive_uploaded": False,
    }
