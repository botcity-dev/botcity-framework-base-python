import inspect
import os
import pathlib
import sys
from os import path

from PIL import Image


class BaseBot:
    def action(self, execution=None):
        """
        Execute an automation action.

        Args:
            execution (BotExecution, optional): Information about the execution when running
                this bot in connection with the BotCity Maestro Orchestrator.
        """
        raise NotImplementedError("You must implement this method.")

    def get_resource_abspath(self, filename, resource_folder="resources"):
        """
        Compose the resource absolute path taking into account the package path.

        Args:
            filename (str): The filename under the resources folder.
            resource_folder (str, optional): The resource folder name. Defaults to `resources`.

        Returns:
            abs_path (str): The absolute path to the file.
        """
        return path.join(self._resources_path(resource_folder), filename)

    def _resources_path(self, resource_folder="resources"):
        # This checks if this is a pyinstaller binary
        # More info here: https://pyinstaller.org/en/stable/runtime-information.html#run-time-information
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            klass_name = self.__class__.__name__
            res_path = os.path.join(sys._MEIPASS, klass_name, "resources")
        else:
            res_path = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(res_path)), resource_folder)

    def _search_image_file(self, label):
        """
        When finding images, this is the priority in which we will look into:
            - map_images: This is a highly customized place that takes precedence over everything else
            - If this is not a pyinstaller binary:
                - "resources" folder parallel to the Bot class file.
                - "resources" folder parallel to the `find` caller file. (cookiecutter Both)
                - "resources" folder parallel to the current working dir
            - If this is a pyinstaller binary:
                - "resources" folder at sys._MEIPASS/<package>/
                - "resources" folder parallel to the sys._MEIPASS folder
                - sys._MEIPASS
            - current working dir
        """

        # map_images
        img_path = self.state.map_images.get(label)
        if img_path:
            return img_path

        # list of locations by priority
        locations = []

        # This checks if this is a pyinstaller binary
        # More info here: https://pyinstaller.org/en/stable/runtime-information.html#run-time-information
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):

            # "resources" folder at sys._MEIPASS/<package>/
            locations.append(self.get_resource_abspath(""))
            # "resources" folder parallel to the sys._MEIPASS folder
            locations.append(os.path.join(sys._MEIPASS, "resources"))
            # sys._MEIPASS
            locations.append(sys._MEIPASS)
        else:
            # This is a regular project not binary file.

            # "resources" folder parallel to the Bot class file.
            locations.append(self.get_resource_abspath(""))

            # "resources" folder parallel to the `find` caller file.
            try:
                caller = inspect.currentframe().f_back.f_back
                caller_filename = inspect.getframeinfo(caller).filename
                caller_dir = os.path.dirname(caller_filename)
                locations.append(os.path.join(caller_dir, "resources"))
            except:  # noqa: E722
                pass

        # "resources" folder parallel to the current working dir
        locations.append(os.path.join(os.getcwd(), "resources"))

        # current working dir
        locations.append(os.getcwd())

        for sp in locations:
            path = pathlib.Path(sp)
            found = path.glob(f"{label}.*")
            for f in found:
                try:
                    img = Image.open(f)
                except Exception:
                    continue
                else:
                    img.close()
                return str(f.absolute())
        return None

    def _image_path_as_image(self, path):
        if path:
            return Image.open(path)
        return None

    @classmethod
    def main(cls):
        try:
            from botcity.maestro import BotExecution, BotMaestroSDK
            maestro_available = True
        except ImportError:
            maestro_available = False

        bot = cls()
        execution = None
        # TODO: Refactor this later for proper parameters to be passed
        #       in a cleaner way
        if len(sys.argv) == 4:
            if maestro_available:
                server, task_id, token = sys.argv[1:4]
                bot.maestro = BotMaestroSDK(server=server)
                bot.maestro.access_token = token

                parameters = bot.maestro.get_task(task_id).parameters

                execution = BotExecution(server, task_id, token, parameters)
                bot.execution = execution
            else:
                raise RuntimeError("Your setup is missing the botcity-maestro-sdk package. "
                                   "Please install it with: pip install botcity-maestro-sdk")

        bot.action(execution)
