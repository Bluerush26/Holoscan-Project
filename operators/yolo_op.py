from holoscan.core import Operator, OperatorSpec
from ultralytics import YOLO
import torch

class YOLOInferenceOp(Operator):
    def __init__(self, fragment, *args, model_path="yolov11n.pt", **kwargs):
        self.model_path = model_path
        # Forward arguments to the base Operator class
        super().__init__(fragment, *args, **kwargs)

    def setup(self, spec: OperatorSpec):
        # Define an input port for video frames
        spec.input("input_frame")
        # Define an output port for detection results (tensors or objects)
        spec.output("outputs")

    def initialize(self):
        # Load the model into GPU memory once at startup
        self.model = YOLO(self.model_path).to("cuda")
        print(f"Model {self.model_path} loaded successfully.")

    def compute(self, op_input, op_output, context):
        # 1. Receive the message from the previous operator
        message = op_input.receive("input_frame")
        
        # 2. Extract the image tensor (usually a CuPy or Torch tensor)
        # Note: Depending on your upstream op, you might need to convert the message
        frame = message.get("") 

        # 3. Run YOLO Inference
        # We use stream=True for better performance in video pipelines
        results = self.model(frame, verbose=False)

        # 4. Emit the results to the next operator (e.g., a visualizer)
        op_output.emit(results, "outputs")