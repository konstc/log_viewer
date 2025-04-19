""" Unit-tests for settings_dialog.py module entities """

# modules under test
from settings_dialog import SettingsDialog

# pylint: disable-next=unused-argument
def test_settings_dialog_init(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog initialization

    Step 0: Instantiate a SettingsDialog object
    Step 1: Check that passed settings is the same as self._settings
    """
    settings = SettingsDialog(setup_settings_data)
    assert settings.get_settings() == setup_settings_data

# pylint: disable-next=unused-argument
def test_settings_dialog_mode_changed(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog.mode_changed()

    Step 0: Instantiate a SettingsDialog object
    Step 1: Call SettingsDialog.mode_changed(0)
    Step 2: Check corresponding tabs for enabled state
    Step 3: Call SettingsDialog.mode_changed(1)
    Step 4: Check corresponding tabs for enabled state
    Step 5: Call SettingsDialog.mode_changed(2)
    Step 6: Check corresponding tabs for enabled state
    """
    settings = SettingsDialog(setup_settings_data)
    # pylint: disable=protected-access
    settings.mode_changed(0)
    assert settings._ui.tabWidget.isTabEnabled(1)
    assert not settings._ui.tabWidget.isTabEnabled(2)
    settings.mode_changed(1)
    assert not settings._ui.tabWidget.isTabEnabled(1)
    assert settings._ui.tabWidget.isTabEnabled(2)
    settings.mode_changed(2)
    assert not settings._ui.tabWidget.isTabEnabled(1)
    assert not settings._ui.tabWidget.isTabEnabled(2)

# pylint: disable-next=unused-argument
def test_settings_dialog_use_mpl_toolbar_changed(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog.use_mpl_toolbar_changed()

    Step 0: Instantiate a SettingsDialog object
    Step 1: Call SettingsDialog.use_mpl_toolbar_changed(2)
    Step 2: Check that corresponding QComboBoxes are disabled
    Step 3: Call SettingsDialog.use_mpl_toolbar_changed(0)
    Step 4: Check that corresponding QComboBoxes are enabled
    """
    settings = SettingsDialog(setup_settings_data)
    # pylint: disable=protected-access
    settings.use_mpl_toolbar_changed(2)
    assert not settings._ui.cursorStyleSelectorBox.isEnabled()
    assert not settings._ui.cursorWidthSelectorBox.isEnabled()
    assert not settings._ui.cursorColorSelectorBox.isEnabled()
    settings.use_mpl_toolbar_changed(0)
    assert settings._ui.cursorStyleSelectorBox.isEnabled()
    assert settings._ui.cursorWidthSelectorBox.isEnabled()
    assert settings._ui.cursorColorSelectorBox.isEnabled()

# pylint: disable-next=unused-argument
def test_settings_dialog_scale_funcs(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog.add_scale(), SettingsDialog.remove_scale(),
        SettingsDialog.clear_scales()
    
    Step 0: Instantiate a SettingsDialog object
    Step 1: Call SettingsDialog.add_scale() twice
    Step 2: Check that SettingsDialog._scale_name_edits and 
        SettingsDialog._scale_value_edits are 2
    Step 3: Call SettingsDialog.remove_scale()
    Step 4: Check that SettingsDialog._scale_name_edits and 
        SettingsDialog._scale_value_edits are 2
    Step 5: Select row #0
    Step 6: Call SettingsDialog.remove_scale()
    Step 7: Check that SettingsDialog._scale_name_edits and 
        SettingsDialog._scale_value_edits are 1
    Step 8: Call SettingsDialog.clear_scales()
    Step 9: Check that SettingsDialog._scale_name_edits and 
        SettingsDialog._scale_value_edits are 0
    """
    settings = SettingsDialog(setup_settings_data)
    # pylint: disable=protected-access
    settings.add_scale()
    settings.add_scale()
    assert len(settings._scale_name_edits) == 2
    assert len(settings._scale_value_edits) == 2
    settings.remove_scale()
    assert len(settings._scale_name_edits) == 2
    assert len(settings._scale_value_edits) == 2
    settings._ui.scaleTable.selectRow(0)
    settings.remove_scale()
    assert len(settings._scale_name_edits) == 1
    assert len(settings._scale_value_edits) == 1
    settings.clear_scales()
    assert len(settings._scale_name_edits) == 0
    assert len(settings._scale_value_edits) == 0

# pylint: disable-next=unused-argument
def test_settings_dialog_db_funcs(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog.clear_db()

    Step 0: Instantiate a SettingsDialog object
    Step 1: Call SettingsDialog._ui.databaseList.addItem()
    Step 2: Check that SettingsDialog._ui.databaseList.count() is 1
    Step 3: Call SettingsDialog.clear_db()
    Step 4: Check that SettingsDialog._ui.databaseList.count() is 0
    """
    settings = SettingsDialog(setup_settings_data)
    # pylint: disable=protected-access
    settings._ui.databaseList.addItem("db0")
    assert settings._ui.databaseList.count() == 1
    settings.clear_db()
    assert settings._ui.databaseList.count() == 0

# pylint: disable-next=unused-argument
def test_settings_dialog_save_settings(setup_settings_data, qtbot):
    """
    Unit-tests for SettingsDialog.save_settings()

    Step 0: Instantiate a SettingsDialog object
    Step 1: Call SettingsDialog.save_settings()
    Step 2: Check that saved settings is the same as setup_settings_data
    """
    settings = SettingsDialog(setup_settings_data)
    # pylint: disable=protected-access
    settings.save_settings()
    assert settings.get_settings() == setup_settings_data
