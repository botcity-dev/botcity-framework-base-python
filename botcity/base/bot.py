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
        path_to_class = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(path_to_class)), resource_folder)

    def _search_image_file(self, label):
        img_path = self.state.map_images.get(label)
        if img_path:
            return img_path

        search_path = [self.get_resource_abspath(""), os.getcwd()]
        for sp in search_path:
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

    @classmethod
    def main(cls):
        try:
            from botcity.maestro import BotMaestroSDK, BotExecution
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
            else:
                raise RuntimeError("Your setup is missing the botcity-maestro-sdk package. "
                                   "Please install it with: pip install botcity-maestro-sdk")

        bot.action(execution)
