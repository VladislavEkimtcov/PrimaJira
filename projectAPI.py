import win32com.client

class ProjectInterface:
    """
    Microsoft Project interfacing class
    Supports Project 2016, others unproven
    Needs project installed
    """
    def __init__(self, filePath):
        msp = win32com.client.gencache.EnsureDispatch("MSProject.Application")
        msp.FileOpen(filePath)
        self.project = msp.ActiveProject

    def fetch_tasks(self):
        return self.project.Tasks
