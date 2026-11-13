class LayerTamperedException(Exception):
    """Occurs when trying to drag-and-drop a layer, but that layer isn't in the list it used to be in"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
