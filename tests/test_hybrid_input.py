import asyncio
import contextlib
import sys
import unittest
from multiprocessing import Array, Value
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from televuer.televuer import TeleVuer
from televuer.tv_wrapper import TeleVuerWrapper


class HybridInputTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def hybrid_tvuer():
        tvuer = TeleVuer.__new__(TeleVuer)
        tvuer.use_hand_tracking = True
        tvuer.use_controller_input = True
        tvuer.left_arm_pose_shared = Array('d', [1.0] * 16, lock=True)
        tvuer.right_arm_pose_shared = Array('d', [2.0] * 16, lock=True)
        tvuer.motion_data_ready_shared = Value('b', False, lock=True)
        tvuer.left_controller_data_updated_at_shared = Value('d', 0.0, lock=True)
        tvuer.controller_data_updated_at_shared = Value('d', 0.0, lock=True)
        for prefix in ("left", "right"):
            for name in ("trigger", "squeeze", "thumbstick", "aButton", "bButton"):
                setattr(tvuer, f"{prefix}_ctrl_{name}_shared", Value('b', False, lock=True))
            for name in ("triggerValue", "squeezeValue"):
                setattr(tvuer, f"{prefix}_ctrl_{name}_shared", Value('d', 0.0, lock=True))
            setattr(tvuer, f"{prefix}_ctrl_thumbstickValue_shared", Array('d', 2, lock=True))
        return tvuer

    async def test_right_only_controller_event_does_not_replace_hand_arm_pose(self):
        tvuer = self.hybrid_tvuer()
        event = type("Event", (), {"value": {
            "right": [4.0] * 16,
            "rightState": {"thumbstickValue": [0.5, 0.0], "aButton": True},
        }})()

        await tvuer.on_controller_move(event, None)

        self.assertEqual(list(tvuer.left_arm_pose_shared), [1.0] * 16)
        self.assertEqual(list(tvuer.right_arm_pose_shared), [2.0] * 16)
        self.assertFalse(tvuer.motion_data_ready_shared.value)
        np.testing.assert_allclose(tvuer.left_ctrl_thumbstickValue, [0.0, 0.0])
        np.testing.assert_allclose(tvuer.right_ctrl_thumbstickValue, [0.5, 0.0])
        self.assertTrue(tvuer.right_ctrl_aButton)
        self.assertEqual(tvuer.left_controller_data_updated_at, 0.0)
        self.assertGreater(tvuer.controller_data_updated_at, 0.0)
        self.assertEqual(tvuer.right_controller_data_updated_at, tvuer.controller_data_updated_at)

    async def test_left_only_controller_event_refreshes_only_left_freshness(self):
        tvuer = self.hybrid_tvuer()
        event = type("Event", (), {"value": {
            "leftState": {"thumbstickValue": [-0.25, -0.75]},
        }})()

        await tvuer.on_controller_move(event, None)

        np.testing.assert_allclose(tvuer.left_ctrl_thumbstickValue, [-0.25, -0.75])
        self.assertGreater(tvuer.left_controller_data_updated_at, 0.0)
        self.assertEqual(tvuer.right_controller_data_updated_at, 0.0)
        self.assertEqual(tvuer.controller_data_updated_at, 0.0)

    async def test_hybrid_scene_mounts_hands_and_controllers(self):
        tvuer = TeleVuer.__new__(TeleVuer)
        tvuer.use_hand_tracking = True
        tvuer.use_controller_input = True
        tvuer.use_body_tracking = False
        tvuer.display_fps = 30.0
        nodes = []
        session = SimpleNamespace(upsert=lambda node, **kwargs: nodes.append(type(node).__name__))

        task = asyncio.create_task(tvuer.main_pass_through(session))
        await asyncio.sleep(0)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        self.assertEqual(nodes, ["Hands", "MotionControllers"])

    def test_hand_teledata_includes_controller_axes(self):
        tvuer = SimpleNamespace(
            head_pose=np.eye(4), left_arm_pose=np.eye(4), right_arm_pose=np.eye(4),
            left_hand_positions=np.zeros((25, 3)), right_hand_positions=np.zeros((25, 3)),
            motion_data_ready=True, body_tracking_ready=False,
            controller_data_updated_at=123.0,
            left_controller_data_updated_at=122.0,
            right_controller_data_updated_at=123.0,
            left_hand_pinch=False, left_hand_pinchValue=0.0,
            left_hand_squeeze=False, left_hand_squeezeValue=0.0,
            right_hand_pinch=False, right_hand_pinchValue=0.0,
            right_hand_squeeze=False, right_hand_squeezeValue=0.0,
            left_ctrl_trigger=False, left_ctrl_triggerValue=0.0,
            left_ctrl_squeeze=False, left_ctrl_squeezeValue=0.0,
            left_ctrl_aButton=False, left_ctrl_bButton=False, left_ctrl_thumbstick=False,
            left_ctrl_thumbstickValue=np.array([-0.25, -0.75]),
            right_ctrl_trigger=False, right_ctrl_triggerValue=0.0,
            right_ctrl_squeeze=False, right_ctrl_squeezeValue=0.0,
            right_ctrl_aButton=False, right_ctrl_bButton=False, right_ctrl_thumbstick=False,
            right_ctrl_thumbstickValue=np.array([0.5, 0.0]),
        )

        wrapper = TeleVuerWrapper.__new__(TeleVuerWrapper)
        wrapper.use_hand_tracking = True
        wrapper.use_body_tracking = False
        wrapper.use_controller_input = True
        wrapper.return_hand_rot_data = False
        wrapper.arm_reference_mode = "head_yaw"
        wrapper.tvuer = tvuer

        tele_data = wrapper.get_tele_data()

        np.testing.assert_allclose(tele_data.left_ctrl_thumbstickValue, [-0.25, -0.75])
        np.testing.assert_allclose(tele_data.right_ctrl_thumbstickValue, [0.5, 0.0])
        self.assertEqual(tele_data.left_controller_data_updated_at, 122.0)
        self.assertEqual(tele_data.right_controller_data_updated_at, 123.0)
        self.assertEqual(tele_data.controller_data_updated_at, 123.0)


if __name__ == "__main__":
    unittest.main()
