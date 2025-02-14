from django.apps import AppConfig

# logger = logging.getLogger(__name__)


class MainConfig(AppConfig):
    name = "main"

    def ready(self):
        from icecream import ic

        ic.configureOutput(includeContext=True)
