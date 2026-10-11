"""Joint order emitted by Vuer 0.1.6's BODY_MOVE body array."""

BODY_JOINT_KEYS = (
    "hips", "spine-lower", "spine-middle", "spine-upper", "chest", "neck", "head",
    "left-shoulder", "left-scapula", "left-arm-upper", "left-arm-lower", "left-hand-wrist-twist",
    "right-shoulder", "right-scapula", "right-arm-upper", "right-arm-lower", "right-hand-wrist-twist",
    "left-hand-palm", "right-hand-palm",
    "left-upper-leg", "left-lower-leg", "left-foot-ankle-twist", "left-foot-ankle",
    "left-foot-subtalar", "left-foot-transverse", "left-foot-ball",
    "right-upper-leg", "right-lower-leg", "right-foot-ankle-twist", "right-foot-ankle",
    "right-foot-subtalar", "right-foot-transverse", "right-foot-ball",
)

BODY_JOINT_INDEX = {name: index for index, name in enumerate(BODY_JOINT_KEYS)}
ARM_BODY_JOINTS = (
    "left-shoulder", "left-arm-lower", "left-hand-wrist-twist",
    "right-shoulder", "right-arm-lower", "right-hand-wrist-twist",
)
