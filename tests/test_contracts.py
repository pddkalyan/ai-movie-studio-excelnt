"""Offline acceptance tests: planning contracts, not generated film evidence."""
import dataclasses
import unittest

from studio.contracts import PlanError
from studio.planning import build_example_episode, summarize_plan
from studio.provider_contract import DisabledProvider, ProviderUnavailable, GenerationRequest


class CinematicContractTests(unittest.TestCase):
    def setUp(self):
        self.episode = build_example_episode()

    def test_exact_twenty_minutes_and_16_by_9(self):
        p = self.episode
        p.validate()
        self.assertEqual(p.planned_frames, 28800)
        self.assertEqual(p.shot_count, 120)
        self.assertEqual((p.width, p.height, p.fps), (1920, 1080, 24))
        self.assertEqual(len(p.scenes), 12)
        self.assertEqual(p.duration_seconds, 1200)

    def test_demonstration_cannot_masquerade_as_rendered_movie(self):
        info = summarize_plan(self.episode)
        self.assertTrue(info["plan_only"])
        self.assertEqual(info["rendered_clips"], 0)
        self.assertFalse(info["archive_uploaded"])
        self.assertFalse(info["verified_audio"])

    def test_reject_shorter_than_twenty_minutes(self):
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, duration_seconds=1199).validate()

    def test_reject_non_16_by_9(self):
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, width=1000).validate()

    def test_reject_overlap_in_timeline(self):
        first = self.episode.scenes[0]
        bad_shots = (first.shots[0], dataclasses.replace(first.shots[1], start_frame=1)) + first.shots[2:]
        modified = dataclasses.replace(first, shots=bad_shots)
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(modified,) + self.episode.scenes[1:]).validate()

    def test_reject_missing_frame_at_end(self):
        last_scene = self.episode.scenes[-1]
        modified = dataclasses.replace(last_scene, shots=last_scene.shots[:-1])
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=self.episode.scenes[:-1] + (modified,)).validate()

    def test_reject_unknown_character(self):
        scene = self.episode.scenes[0]
        shot = dataclasses.replace(scene.shots[0], visible_character_ids=("unknown",),
                                   dialogue_speaker_id=None, reference_asset_ids=())
        bad = dataclasses.replace(scene, shots=(shot,) + scene.shots[1:])
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(bad,) + self.episode.scenes[1:]).validate()

    def test_reject_missing_visual_continuity_reference(self):
        scene = self.episode.scenes[0]
        shot = dataclasses.replace(scene.shots[0], reference_asset_ids=("reference_hero_v1",))
        bad = dataclasses.replace(scene, shots=(shot,) + scene.shots[1:])
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(bad,) + self.episode.scenes[1:]).validate()

    def test_reject_speaker_not_visible(self):
        scene = self.episode.scenes[0]
        shot = dataclasses.replace(scene.shots[0], visible_character_ids=("partner",), dialogue_speaker_id="hero")
        bad = dataclasses.replace(scene, shots=(shot,) + scene.shots[1:])
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(bad,) + self.episode.scenes[1:]).validate()

    def test_reject_duplicate_voice_identity(self):
        char = dataclasses.replace(self.episode.characters[1], voice_profile_id="voice_hero_v1")
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, characters=(self.episode.characters[0], char)).validate()

    def test_reject_duplicate_shot_identity(self):
        scene = self.episode.scenes[0]
        shots = (scene.shots[0], dataclasses.replace(scene.shots[1], shot_id=scene.shots[0].shot_id)) + scene.shots[2:]
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(dataclasses.replace(scene, shots=shots),) + self.episode.scenes[1:]).validate()

    def test_reject_shot_longer_than_fifteen_seconds(self):
        scene = self.episode.scenes[0]
        shot = dataclasses.replace(scene.shots[0], frame_count=24 * 16)
        bad = dataclasses.replace(scene, shots=(shot,) + scene.shots[1:])
        with self.assertRaises(PlanError):
            dataclasses.replace(self.episode, scenes=(bad,) + self.episode.scenes[1:]).validate()

    def test_zero_default_render_provider(self):
        request = GenerationRequest("shot_01_01", "Example only", ("reference_hero_v1",),
                                    240, 24, "image_to_video")
        with self.assertRaises(ProviderUnavailable):
            DisabledProvider().generate(request)


if __name__ == "__main__":
    unittest.main()
