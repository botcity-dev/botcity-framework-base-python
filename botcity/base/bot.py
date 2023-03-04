import inspect
import os
import pathlib
import sys
from os import path

from PIL import Image


class BaseBot:

    def __init__(self, *args, **kwargs):
        self._resource_folder_name = "resources"

    @property
    def resource_folder_name(self) -> str:
        """The name used for the resources folder
        when looking for files.

        Returns:
            str: The folder name for resources. Defaults to `resources`
        """
        if not hasattr(self, "_resource_folder_name"):
            self._resource_folder_name = "resources"
        return self._resource_folder_name or "resources"

    @resource_folder_name.setter
    def resource_folder_name(self, name: str):
        """The name used for the resources folder
        whe looking for files.

        Args:
            name (str): The folder name for resources. Defaults to `resources`
        """
        if not name:
            raise ValueError("Resources folder name must not be None nor empty.")
        self._resource_folder_name = name

    def action(self, execution=None):
        """
        Execute an automation action.

        Args:
            execution (BotExecution, optional): Information about the execution when running
                this bot in connection with the BotCity Maestro Orchestrator.
        """
        raise NotImplementedError("You must implement this method.")

    def get_resource_abspath(self, filename, resource_folder=None):
        """
        Compose the resource absolute path taking into account the package path.

        Args:
            filename (str): The filename under the resources folder.
            resource_folder (str, optional): The resource folder name. Defaults to `resources`.

        Returns:
            abs_path (str): The absolute path to the file.
        """
        for loc in self._get_resource_locations(resource_folder=resource_folder):
            res_path = pathlib.Path(loc, filename)
            if res_path.exists():
                return str(res_path.absolute())
        return None

    def _resources_path(self, resource_folder=None):
        # This checks if this is a pyinstaller binary
        # More info here: https://pyinstaller.org/en/stable/runtime-information.html#run-time-information
        resource_folder = resource_folder or self.resource_folder_name

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            klass_name = self.__class__.__name__
            res_path = os.path.join(sys._MEIPASS, klass_name, resource_folder)
        else:
            res_path = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(res_path)), resource_folder)

    def _get_frame_path(self, frame):
        frame_filename = inspect.getframeinfo(frame).filename
        frame_dir = os.path.dirname(frame_filename)
        return frame_dir

    def _get_resource_locations(self, resource_folder=None):
        resource_folder = resource_folder or self.resource_folder_name

        # list of locations by priority
        locations = []

        # This checks if this is a pyinstaller binary
        # More info here: https://pyinstaller.org/en/stable/runtime-information.html#run-time-information
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):

            # "resources" folder at sys._MEIPASS/<package>/
            locations.append(self._resources_path(resource_folder=resource_folder))
            # "resources" folder parallel to the sys._MEIPASS folder
            locations.append(os.path.join(sys._MEIPASS, resource_folder))
            # sys._MEIPASS
            locations.append(sys._MEIPASS)
        else:
            # This is a regular project not binary file.

            # "resources" folder parallel to the Bot class file.
            locations.append(self._resources_path(resource_folder=resource_folder))

            # "resources" folder parallel to the `find` caller file.
            try:
                frame = inspect.currentframe()
                while frame is not None:
                    caller_dir = self._get_frame_path(frame)
                    caller_path = os.path.join(caller_dir, resource_folder)
                    locations.append(caller_path)
                    frame = frame.f_back
            except:  # noqa: E722
                pass

        # "resources" folder parallel to the current working dir
        locations.append(os.path.join(os.getcwd(), resource_folder))

        # current working dir
        locations.append(os.getcwd())
        return locations

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
        # map_imagescar
        img_path = self.state.map_images.get(label)
        if img_path:
            return img_path

        # list of locations by priority
        locations = self._get_resource_locations()

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
        if len(sys.argv) >= 4:
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
