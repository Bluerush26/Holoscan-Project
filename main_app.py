# app.py
from holoscan.core import Application
from holoscan.operators import VideoStreamReplayerOp, FormatConverterOp
from operators.yolo_op import YOLOInferenceOp
from operators.navigation_op import NavigationOp

class SecondSightApp(Application):
    def compose(self):

        # Video source simulating glasses
        video = VideoStreamReplayerOp(
            self,
            name="video_source",
            directory="data",
            basename="tester",
            extension=".mp4",
            loop=True
        )

        # Convert to GPU-friendly format
        converter = FormatConverterOp(self, name="converter")

        # YOLO inference
        yolo = YOLOInferenceOp(self, name="yolo_inference")

        # Directional guidance
        nav = NavigationOp(self, name="navigation")

        # Connect the flow
        self.add_flow(video, converter)
        self.add_flow(converter, yolo)
        self.add_flow(yolo, nav)

if __name__ == "__main__":
    app = SecondSightApp()
    app.run()