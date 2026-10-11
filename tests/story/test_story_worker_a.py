"""EX-A-0002: deterministic negative and positive Movie Bible tests, zero model calls."""
import dataclasses
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.story import (AssetReference, CharacterProfile, LocationProfile, MovieBible,
                          StoryError, StoryPlan, example_story_plan)
from studio.story.continuity import CharacterAppearance, DialogueLine
from studio.story.journal import StoryJournal, StoryReceipt


def reference(name="hero", version=1, sha="a"):
    return AssetReference(name + "_visual", version, sha * 64)


def bible():
    return MovieBible("bible_one", 1, "The Hidden Door", "探索 the underwater archive.", (
        CharacterProfile("hero", "lead", "Karthik", "voice_hero", reference("hero"), "costume_blue", ("compass",)),
        CharacterProfile("partner", "ally", "Meera", "voice_partner", reference("partner", sha="b"), "costume_red", ("key",)),
    ), (LocationProfile("undersea", "Ancient submerged temple", reference("undersea", sha="c")),))


def replace_shot(plan, change):
    scene=plan.scenes[0]
    shot=change(scene.shots[0])
    scene=dataclasses.replace(scene, shots=(shot,)+scene.shots[1:])
    return dataclasses.replace(plan, scenes=(scene,)+plan.scenes[1:])


def replace_scene(plan, change):
    return dataclasses.replace(plan, scenes=(change(plan.scenes[0]),)+plan.scenes[1:])


class StoryContractTests(unittest.TestCase):
    def setUp(self):
        self.bible=bible()
        self.plan=example_story_plan(self.bible)

    def assert_bad(self, plan):
        with self.assertRaises(StoryError): plan.validate(self.bible)

    def test_example_twenty_minutes_and_frame_continuity(self):
        self.plan.validate(self.bible)
        self.assertEqual(len(self.plan.scenes),12)
        self.assertEqual(sum(len(s.shots) for s in self.plan.scenes),120)
        self.assertEqual(self.plan.scenes[-1].shots[-1].start_frame+240,28800)
        self.assertEqual(self.plan.duration_seconds,1200)
        self.assertEqual((self.plan.width,self.plan.height,self.plan.fps),(1920,1080,24))

    def test_deterministic_bible_and_plan_hash(self):
        self.assertEqual(self.bible.digest(),bible().digest())
        self.assertEqual(self.plan.digest(self.bible),example_story_plan(bible()).digest(bible()))

    def test_unicode_titles_and_dialogue(self):
        b=dataclasses.replace(self.bible,title="काशी: 旅のはじまり")
        p=example_story_plan(b)
        self.assertEqual(p.bible_digest_sha256,b.digest())
        p.validate(b)

    def test_frozen_bible_and_shots(self):
        with self.assertRaises(dataclasses.FrozenInstanceError): self.bible.title="new"
        with self.assertRaises(dataclasses.FrozenInstanceError): self.plan.scenes[0].shots[0].frame_count=0

    def test_duplicate_character_id_rejected(self):
        b=dataclasses.replace(self.bible,characters=(self.bible.characters[0],self.bible.characters[0]))
        with self.assertRaises(StoryError): b.validate()

    def test_duplicate_role_id_rejected(self):
        c=dataclasses.replace(self.bible.characters[1],role_id="lead")
        with self.assertRaises(StoryError): dataclasses.replace(self.bible,characters=(self.bible.characters[0],c)).validate()

    def test_duplicate_voice_id_rejected(self):
        c=dataclasses.replace(self.bible.characters[1],voice_id="voice_hero")
        with self.assertRaises(StoryError): dataclasses.replace(self.bible,characters=(self.bible.characters[0],c)).validate()

    def test_stale_bible_revision_rejected(self):
        b=dataclasses.replace(self.bible,revision=2)
        with self.assertRaises(StoryError): self.plan.validate(b)

    def test_bible_modified_without_revision_rejected(self):
        b=dataclasses.replace(self.bible,title="Different title")
        with self.assertRaises(StoryError): self.plan.validate(b)

    def test_visual_version_drift_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,appearances=(
            dataclasses.replace(shot.appearances[0],visual=dataclasses.replace(shot.appearances[0].visual,version=2)),)+shot.appearances[1:])))

    def test_visual_sha_drift_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,appearances=(
            dataclasses.replace(shot.appearances[0],visual=dataclasses.replace(shot.appearances[0].visual,checksum_sha256="f"*64)),)+shot.appearances[1:])))

    def test_costume_drift_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,appearances=(
            dataclasses.replace(shot.appearances[0],costume_id="costume_black"),)+shot.appearances[1:])))

    def test_prop_drift_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,appearances=(
            dataclasses.replace(shot.appearances[0],carried_props=("unapproved_prop",)),)+shot.appearances[1:])))

    def test_duplicate_prop_rejected(self):
        c=dataclasses.replace(self.bible.characters[0],canonical_prop_ids=("compass","compass"))
        with self.assertRaises(StoryError): dataclasses.replace(self.bible,characters=(c,self.bible.characters[1])).validate()

    def test_location_wrong_reference_rejected(self):
        self.assert_bad(replace_scene(self.plan,lambda scene: dataclasses.replace(scene,location_visual=reference("elsewhere"))))

    def test_location_wrong_version_rejected(self):
        self.assert_bad(replace_scene(self.plan,lambda scene: dataclasses.replace(scene,location_visual=dataclasses.replace(scene.location_visual,version=4))))

    def test_location_unknown_rejected(self):
        self.assert_bad(replace_scene(self.plan,lambda scene: dataclasses.replace(scene,location_id="unknown")))

    def test_wrong_voice_id_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,dialogue=(
            dataclasses.replace(shot.dialogue[0],voice_id="voice_partner"),))))

    def test_invisible_speaker_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,
            appearances=shot.appearances[1:],dialogue=(dataclasses.replace(shot.dialogue[0],speaker_character_id="hero"),))))

    def test_unknown_character_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,
            appearances=(dataclasses.replace(shot.appearances[0],character_id="intruder"),)+shot.appearances[1:])))

    def test_duplicate_onscreen_character_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot: dataclasses.replace(shot,
            appearances=(shot.appearances[0],shot.appearances[0]))))

    def test_duplicate_dialogue_line_across_shots_rejected(self):
        scene=self.plan.scenes[0]
        second=dataclasses.replace(scene.shots[1],dialogue=(scene.shots[0].dialogue[0],))
        self.assert_bad(replace_scene(self.plan,lambda sc:dataclasses.replace(sc,shots=(sc.shots[0],second)+sc.shots[2:])))

    def test_broken_scene_order_rejected(self):
        self.assert_bad(replace_scene(self.plan,lambda scene:dataclasses.replace(scene,ordinal=2)))

    def test_duplicate_scene_id_rejected(self):
        second=dataclasses.replace(self.plan.scenes[1],scene_id="scene_01")
        self.assert_bad(dataclasses.replace(self.plan,scenes=(self.plan.scenes[0],second)+self.plan.scenes[2:]))

    def test_duplicate_shot_id_across_scenes_rejected(self):
        second=self.plan.scenes[1]
        first_shot=dataclasses.replace(second.shots[0],shot_id="shot_01_01")
        second=dataclasses.replace(second,shots=(first_shot,)+second.shots[1:])
        self.assert_bad(dataclasses.replace(self.plan,scenes=(self.plan.scenes[0],second)+self.plan.scenes[2:]))

    def test_gap_in_frames_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot:dataclasses.replace(shot,start_frame=1)))

    def test_overlap_in_frames_rejected(self):
        scene=self.plan.scenes[0]
        second=dataclasses.replace(scene.shots[1],start_frame=100)
        self.assert_bad(replace_scene(self.plan,lambda sc:dataclasses.replace(sc,shots=(sc.shots[0],second)+sc.shots[2:])))

    def test_shortened_episode_rejected(self):
        scene=self.plan.scenes[-1]
        self.assert_bad(dataclasses.replace(self.plan,scenes=self.plan.scenes[:-1]+(dataclasses.replace(scene,shots=scene.shots[:-1]),)))

    def test_long_shot_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot:dataclasses.replace(shot,frame_count=24*16)))

    def test_invalid_fps_or_ratio_rejected(self):
        for kw in ({"fps":25},{"width":1000},{"duration_seconds":1199}):
            with self.subTest(kw=kw):self.assert_bad(dataclasses.replace(self.plan,**kw))

    def test_invalid_unicode_surrogate_rejected(self):
        b=dataclasses.replace(self.bible,title="broken\ud800")
        with self.assertRaises(StoryError):b.validate()

    def test_boolean_version_rejected(self):
        b=dataclasses.replace(self.bible,revision=True)
        with self.assertRaises(StoryError):b.validate()

    def test_unsafe_control_character_rejected(self):
        self.assert_bad(replace_shot(self.plan,lambda shot:dataclasses.replace(shot,direction="bad\x00data")))

    def test_bible_unchanged_by_rejected_plan(self):
        before=self.bible.digest()
        self.test_wrong_voice_id_rejected()
        self.assertEqual(before,self.bible.digest())


class StoryJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.journal=StoryJournal(self.root)
        b=bible();p=example_story_plan(b)
        self.first=StoryReceipt("EX_A_0002","worker/A/ex-a-0002-story-continuity",1,b.digest(),p.digest(b),None,"PLANNED")

    def second(self, status="VALIDATED"):
        return dataclasses.replace(self.first,sequence=2,previous_receipt_sha256=self.first.digest(),status=status)

    def test_first_receipt_is_saved_and_restored(self):
        digest=self.journal.save(self.first)
        self.assertEqual(digest,self.first.digest())
        self.assertEqual(StoryJournal(self.root).load(),self.first)

    def test_exact_replay_is_idempotent(self):
        self.journal.save(self.first)
        before=(self.root/"story_receipt.json").read_bytes()
        self.assertEqual(self.journal.save(self.first),self.first.digest())
        self.assertEqual((self.root/"story_receipt.json").read_bytes(),before)

    def test_valid_next_receipt_chain(self):
        self.journal.save(self.first)
        self.journal.save(self.second())
        self.assertEqual(self.journal.load().sequence,2)

    def test_conflicting_same_sequence_blocked(self):
        self.journal.save(self.first)
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.first,status="BLOCKED"))

    def test_skipped_sequence_blocked(self):
        self.journal.save(self.first)
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.second(),sequence=3))

    def test_wrong_previous_digest_blocked(self):
        self.journal.save(self.first)
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.second(),previous_receipt_sha256="f"*64))

    def test_wrong_task_or_branch_blocked(self):
        self.journal.save(self.first)
        for changes in ({"task_id":"OTHER"},{"branch":"worker/B/other"}):
            with self.subTest(changes=changes),self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.second(),**changes))

    def test_new_bible_digest_under_old_task_blocked(self):
        self.journal.save(self.first)
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.second(),bible_digest_sha256="f"*64))

    def test_corrupt_json_not_clobbered(self):
        path=self.root/"story_receipt.json"
        raw=b'{"broken": SECRET'
        path.write_bytes(raw)
        with self.assertRaises(StoryError):self.journal.save(self.first)
        self.assertEqual(path.read_bytes(),raw)

    def test_missing_required_field_not_synthesized(self):
        path=self.root/"story_receipt.json"
        raw=json.dumps({"task_id":"EX_A_0002"}).encode()
        path.write_bytes(raw)
        with self.assertRaises(StoryError):self.journal.load()
        self.assertEqual(path.read_bytes(),raw)

    def test_extra_field_rejected(self):
        record=dataclasses.asdict(self.first)
        record["secret"]="untrusted"
        path=self.root/"story_receipt.json"
        raw=json.dumps(record).encode()
        path.write_bytes(raw)
        with self.assertRaises(StoryError):self.journal.load()
        self.assertEqual(path.read_bytes(),raw)

    def test_atomic_disk_failure_preserves_prior_checkpoint(self):
        self.journal.save(self.first)
        path=self.root/"story_receipt.json"
        old=path.read_bytes()
        with patch("studio.story.journal.os.replace",side_effect=OSError("disk full")):
            with self.assertRaises(OSError):self.journal.save(self.second())
        self.assertEqual(path.read_bytes(),old)
        self.assertEqual(list(self.root.glob("*.tmp")),[])
        self.assertFalse((self.root/"story_receipt.lock").exists())

    def test_orphan_lock_blocks(self):
        (self.root/"story_receipt.lock").mkdir()
        with self.assertRaises(StoryError):self.journal.save(self.first)

    def test_invalid_genesis_chain_rejected(self):
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.first,previous_receipt_sha256="a"*64))

    def test_invalid_bool_sequence_rejected(self):
        with self.assertRaises(StoryError):self.journal.save(dataclasses.replace(self.first,sequence=True))

    def test_no_key_or_external_connection(self):
        self.journal.save(self.first)
        raw=(self.root/"story_receipt.json").read_text()
        self.assertNotIn("EXCELNT",raw)
        self.assertNotIn("api_key",raw)

if __name__=="__main__":unittest.main()
