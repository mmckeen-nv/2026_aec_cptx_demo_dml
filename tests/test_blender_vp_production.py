import importlib.util
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills" / "blender_vp_production.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("blender_vp_production_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BlenderVpProductionTests(unittest.TestCase):
    def test_legacy_cleanup_never_targets_valid_handoff(self):
        helper = load_helper()
        self.assertIn("vp_studio_01_export", helper.LEGACY_SCENE_OBJECTS)
        self.assertNotIn("VP_STUDIO_RHINO", helper.LEGACY_SCENE_OBJECTS)
        self.assertFalse(any("vp_studio_rhino".startswith(prefix)
                             for prefix in helper.LEGACY_SCENE_PREFIXES))

    def test_manifest_camera_presets_are_exact_metre_conversions(self):
        helper = load_helper()
        expected = {
            "stage_wide": ((0.0, -14.9352, 3.6576), (-3.048, 3.048, 2.4384), 20.0),
            "stage_three_quarter": ((15.24, -14.9352, 4.2672), (-3.048, 3.048, 2.7432), 24.0),
            "hero": ((-3.048, -10.668, 1.6764), (-3.048, -1.524, 1.8288), 28.0),
            "diagonal": ((15.24, -13.716, 3.048), (-3.048, 0.0, 1.8288), 24.0),
            "control_room": ((19.05, 17.3736, 1.6764), (-3.048, 0.0, 1.8288), 28.0),
        }
        for key, (location, target, lens) in expected.items():
            preset = helper.CAMERA_PRESETS_INCHES[key]
            converted_location = tuple(v * helper.INCH_TO_METER for v in preset["location"])
            converted_target = tuple(v * helper.INCH_TO_METER for v in preset["target"])
            for actual, wanted in zip(converted_location, location):
                self.assertAlmostEqual(wanted, actual, places=6)
            for actual, wanted in zip(converted_target, target):
                self.assertAlmostEqual(wanted, actual, places=6)
            self.assertEqual(lens, preset["lens_mm"])
            self.assertIn("hide_for_render", preset)

    def test_cached_assets_have_locked_real_world_dimensions_and_anchors(self):
        helper = load_helper()
        expected = {
            "camera_tripod_silver_key": ((48.0, 48.0, 72.0), "world_floor"),
            "chair_director_creativejenna": ((22.0, 22.0, 36.0), "proxy_floor"),
            "control_monitor_datsketch": ((6.0, 24.0, 18.0), "proxy_top"),
            "roadcase_thomas_kole": ((48.0, 24.0, 30.0), "proxy_floor"),
            "grip_c_stand_kilianpohl": ((36.0, 36.0, 84.0), "proxy_floor"),
            "light_led_soft_panel_roy": ((24.0, 24.0, 72.0), "proxy_floor"),
            "control_server_rack_anais": ((24.0, 42.0, 84.0), "proxy_floor"),
        }
        self.assertEqual(set(expected), set(helper.FIXED_ASSET_PLACEMENT))
        for key, (size, anchor) in expected.items():
            spec = helper.FIXED_ASSET_PLACEMENT[key]
            self.assertEqual(size, spec["target_size_in"])
            self.assertEqual(anchor, spec["anchor"])
            calculated = tuple(
                source * scale / helper.INCH_TO_METER
                for source, scale in zip(spec["source_size_m"], spec["scale_xyz"])
            )
            for actual, wanted in zip(calculated, size):
                self.assertAlmostEqual(wanted, actual, places=4)

    def test_production_helper_requires_source_stamped_handoff(self):
        helper = load_helper()
        self.assertIn("source_3dm_sha256", HELPER.read_text(encoding="utf-8"))
        self.assertIn("current VP_STUDIO_RHINO handoff is absent or stale", HELPER.read_text(encoding="utf-8"))

    def test_required_set_dressing_is_complete_and_has_no_bare_cstand(self):
        helper = load_helper()
        self.assertEqual(6, len(helper.REQUIRED_SET_DRESSING))
        self.assertEqual(
            27,
            sum(len(proxy_names) for proxy_names in helper.REQUIRED_SET_DRESSING.values()),
        )
        self.assertNotIn("grip_c_stand_kilianpohl", helper.REQUIRED_SET_DRESSING)
        self.assertEqual(
            2,
            len(helper.REQUIRED_SET_DRESSING["light_led_soft_panel_roy"]),
        )
        text = HELPER.read_text(encoding="utf-8")
        self.assertIn("def apply_required_set_dressing", text)
        self.assertIn("VP_SET_DRESSING_PASS categories={}", text)
        self.assertIn("placements={}", text)
        self.assertIn("cameras=3 chairs=8", text)
        self.assertIn("bare C-stand placement is prohibited", text)

    def test_current_handoff_helper_resets_scene_and_requires_led_bounds(self):
        text = HELPER.read_text(encoding="utf-8")
        self.assertIn("def import_current_handoff", text)
        self.assertIn('"LED_ACTIVE_WALL": (0.0, 288.0)', text)
        self.assertIn('"LED_REAR_SUPPORT": (0.0, 312.0)', text)
        self.assertIn("for obj in list(bpy.data.objects)", text)
        self.assertIn("VP_HANDOFF_PASS", text)

    def test_production_look_has_fixed_materials_lights_and_render_gate(self):
        helper = load_helper()
        self.assertEqual(
            {
                "M_LED_Emissive",
                "M_Concrete_Neutral",
                "M_Metal_Dark",
                "M_Fabric_Dark",
                "M_Equipment_Black",
                "M_Wall_Neutral",
                "M_Glass_Clear",
                "M_Proxy_Neutral",
            },
            set(helper.MATERIAL_PALETTE),
        )
        self.assertEqual(5, len(helper.PRODUCTION_LIGHTS))
        text = HELPER.read_text(encoding="utf-8")
        self.assertIn("def prepare_production_look", text)
        self.assertIn("VP_MATERIAL_PASS", text)
        self.assertIn("VP_LIGHTING_PASS", text)
        self.assertIn("VP_RENDER_REJECT", text)
        self.assertIn("min_foreground_fraction", text)
        self.assertIn("min_center_mean", text)
        self.assertIn("max_highlight_fraction", text)
        self.assertIn('setup_manifest_camera("stage_wide"', text)
        self.assertIn("validate_render_image(output_path)", text)

    def test_demo_helper_is_identical_to_tested_root_helper(self):
        demo_helper = (
            ROOT
            / "demos"
            / "virtual_production_studio"
            / "skills"
            / "blender_vp_production.py"
        )
        self.assertEqual(
            hashlib.sha256(HELPER.read_bytes()).hexdigest(),
            hashlib.sha256(demo_helper.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
