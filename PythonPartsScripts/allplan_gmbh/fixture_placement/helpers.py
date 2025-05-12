"""PythonPart fixture placement helper functions"""
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Utility as AllplanUtil


class FileDialogUtil:
    """Helper class for file dialog operations"""
    @staticmethod
    def open_file_dialog(path: str = "") -> str:
        """Open a file dialog to select a file

        Args:
            path: the initial path for the dialog

        Returns:
            The selected file path
        """
        default_dir = AllplanUtil.DefaultDirectories()
        default_dir.AddDirectory(AllplanSettings.AllplanPaths.GetStdPath())
        default_dir.AddDirectory(AllplanSettings.AllplanPaths.GetUsrPath())
        default_dir.AddDirectory(AllplanSettings.AllplanPaths.GetCurPrjPath())

        return AllplanUtil.FileDialog.AskOpenFile(
            path,
            "Select a VS-PythonPart",
            "pyp-files(*.pyp)|*.pyp|",
            "pyp-files(*.pyp)",
            default_dir)
