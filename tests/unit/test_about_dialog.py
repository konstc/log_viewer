""" Unit-tests for about_dialog.py module entities """

# modules under test
from about_dialog import AboutDialog
from version import __version__

# pylint: disable-next=unused-argument
def test_about_dialog(qtbot):
    """
    Unit-tests for AboutDialog methods

    Step 0: Instantiate a MainWindow object
    Step 1: Check that versionLabel contains correct version
    """
    about = AboutDialog()

    # pylint: disable=protected-access
    assert __version__ in about._ui.versionLabel.text()
