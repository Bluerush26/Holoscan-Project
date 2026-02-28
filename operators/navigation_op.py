# operators/navigation_op.py
from holoscan.core import Operator, OperatorSpec

class NavigationOp(Operator):
    """Custom operator that computes direction and prints guidance."""

    def setup(self, spec: OperatorSpec):
        spec.input("detections")

    def compute(self, op_input, op_output, context):
        detections = op_input.receive("detections")
        if not detections:
            return

        # Assume frame center is 640 / 2 for default
        frame_center = 320
        for det in detections:
            offset = det["x_center"] - frame_center
            direction = self.get_direction(offset)
            print(f"{det['label'].capitalize()} {direction}")

    def get_direction(self, offset):
        # Simple threshold-based logic
        if abs(offset) < 50:
            return "ahead"
        elif offset < 0:
            return "slightly left" if abs(offset) < 150 else "far left"
        else:
            return "slightly right" if offset < 150 else "far right"