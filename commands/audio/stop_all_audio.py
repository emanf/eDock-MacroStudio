from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


AudioCategory = MacroCommandCategory("audio", "Audio", "mc:e050")


def stop_all_audio():
    try:
        import pygame
    except ImportError:
        raise RuntimeError("pygame is required. Install it using pip install pygame")

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.stop()
    pygame.mixer.stop()

    return {
        "success": True,
        "playing": False,
    }


class StopAllAudioCommand(MacroCommand):
    id = "audio.stop_all"
    title = "Stop All Audio"
    category = AudioCategory
    icon = "mc:e440"
    description = "Stop all audio started by Macro Studio."
    result_policy = ResultPolicy.DATA
    fields = []

    def display_text(self, values=None):
        return "stop all audio"

    def execute(self, values=None, runtime=None):
        return stop_all_audio()


def register_macro(registry):
    registry.register(StopAllAudioCommand)
