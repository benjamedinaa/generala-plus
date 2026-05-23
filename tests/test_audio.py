import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from generala_plus.audio import SOUND_BUILDERS, SoundManager, audio_dir, ensure_sound_assets


class AudioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_sound_assets_are_generated(self):
        ensure_sound_assets()
        for name in SOUND_BUILDERS:
            path = audio_dir() / f"{name}.wav"
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 64, name)

    def test_sound_manager_volume_controls_are_safe(self):
        manager = SoundManager()
        manager.set_sfx_volume(2)
        manager.set_music_volume(-1)

        self.assertEqual(manager.sfx_volume, 1.0)
        self.assertEqual(manager.music_volume, 0.0)
        manager.toggle_enabled()
        manager.toggle_enabled()


if __name__ == "__main__":
    unittest.main()
