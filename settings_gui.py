import tkinter as tk

# All COCO labels that YOLO can detect, grouped by category
LABEL_GROUPS = {
    "People & Animals": [
        "person", "dog", "cat", "bird", "horse", "sheep", "cow",
        "elephant", "bear", "zebra", "giraffe"
    ],
    "Vehicles": [
        "car", "bicycle", "motorcycle", "bus", "truck", "boat",
        "airplane", "train"
    ],
    "Street & Navigation": [
        "stop sign", "traffic light", "fire hydrant", "parking meter",
        "bench"
    ],
    "Indoor Objects": [
        "chair", "couch", "bed", "dining table", "toilet", "door"
    ],
    "Electronics": [
        "tv", "laptop", "cell phone", "keyboard", "mouse", "remote"
    ],
    "Food & Kitchen": [
        "bottle", "cup", "fork", "knife", "spoon", "bowl",
        "banana", "apple", "sandwich", "pizza"
    ],
    "Other": [
        "backpack", "umbrella", "handbag", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat",
        "skateboard", "surfboard", "tennis racket", "book", "clock",
        "scissors", "teddy bear", "toothbrush", "vase", "potted plant"
    ],
}

# These start checked by default (your original IMPORTANT_OBJECTS)
DEFAULTS = {"person", "car", "chair", "dog", "stop sign", "bicycle", "stairs", "door"}


class SettingsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Eye — Detection Settings")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.check_vars = {}  # label -> BooleanVar

        # --- Header ---
        header = tk.Frame(root, bg="#1e1e2e")
        header.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(
            header, text="👁  Smart Eye Assistant", font=("Helvetica", 18, "bold"),
            fg="#cdd6f4", bg="#1e1e2e"
        ).pack(anchor="w")
        tk.Label(
            header, text="Select the objects you want to be alerted about:",
            font=("Helvetica", 11), fg="#a6adc8", bg="#1e1e2e"
        ).pack(anchor="w", pady=(2, 0))

        # --- Scrollable area ---
        container = tk.Frame(root, bg="#1e1e2e")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container, bg="#1e1e2e", highlightthickness=0, width=520, height=400)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg="#1e1e2e")

        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Build checkboxes per group ---
        for group_name, labels in LABEL_GROUPS.items():
            tk.Label(
                self.inner, text=group_name, font=("Helvetica", 12, "bold"),
                fg="#f38ba8", bg="#1e1e2e", anchor="w"
            ).pack(fill="x", pady=(12, 4))

            row_frame = tk.Frame(self.inner, bg="#1e1e2e")
            row_frame.pack(fill="x")

            for i, label in enumerate(labels):
                var = tk.BooleanVar(value=(label in DEFAULTS))
                self.check_vars[label] = var
                cb = tk.Checkbutton(
                    row_frame, text=label, variable=var,
                    font=("Helvetica", 10), fg="#cdd6f4", bg="#1e1e2e",
                    selectcolor="#313244", activebackground="#1e1e2e",
                    activeforeground="#cdd6f4", anchor="w", width=16
                )
                cb.grid(row=i // 3, column=i % 3, sticky="w", padx=4, pady=1)

        # --- Bottom buttons ---
        btn_frame = tk.Frame(root, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=20, pady=(4, 18))

        tk.Button(
            btn_frame, text="Select All", command=self.select_all,
            font=("Helvetica", 10), bg="#45475a", fg="#cdd6f4",
            activebackground="#585b70", relief="flat", padx=12, pady=4
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_frame, text="Clear All", command=self.clear_all,
            font=("Helvetica", 10), bg="#45475a", fg="#cdd6f4",
            activebackground="#585b70", relief="flat", padx=12, pady=4
        ).pack(side="left")

        tk.Button(
            btn_frame, text="▶  Start Detection", command=self.launch,
            font=("Helvetica", 12, "bold"), bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2d5", relief="flat", padx=20, pady=6
        ).pack(side="right")

    def select_all(self):
        for var in self.check_vars.values():
            var.set(True)

    def clear_all(self):
        for var in self.check_vars.values():
            var.set(False)

    def launch(self):
        selected = [label for label, var in self.check_vars.items() if var.get()]
        if not selected:
            tk.messagebox.showwarning("No labels", "Please select at least one object to detect.")
            return

        self.selected_labels = selected
        print(f"[SETTINGS] Selected {len(selected)} labels: {selected}")
        self.root.destroy()


def open_settings():
    """Opens the settings window and returns the list of selected labels."""
    import tkinter.messagebox
    root = tk.Tk()
    app = SettingsApp(root)
    app.selected_labels = list(DEFAULTS)  # fallback if window is closed
    root.mainloop()
    return app.selected_labels


if __name__ == "__main__":
    selected = open_settings()
    print(f"Selected labels: {selected}")