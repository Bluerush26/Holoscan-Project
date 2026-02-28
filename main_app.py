from holoscan.core import Application
from holoscan.operators import (
    VideoStreamReplayerOp,
    FormatConverterOp,
    InferenceOp
)
# import custom navigation op once made

class AssistiveNavApp(Application):
    def compose(self):
        video = VideoStreamReplayerOp(
            self,
            name="video_source"
            directory="data"
            basename="hallway_demo"
            extension=".mp4"
            loop=True
        )

        convert = FormatConverterOp(self, name="converter")
        infer = InferenceOp(self, name="inference")
        nav = NavigationOp(self, name="navigation")

        self.add_flow(video, convert)
        self.add_flow(convert, infer)
        self.add_flow(infer, nav)

if __name__ == "__main__":
    app = AssistiveNavAp()
    app.run()