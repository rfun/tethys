import unittest
import os
import subprocess
import sys

from unittest import mock
import tethys_apps.cli.init_commands as install_commands

FNULL = open(os.devnull, 'w')


class TestServiceInstallHelpers(unittest.TestCase):

    def test_get_service_from_id_fail(self):
        self.assertFalse(install_commands.get_service_from_id(9384))

    def test_get_service_from_name_fail(self):
        self.assertFalse(install_commands.get_service_from_name("sdfsdf"))

    @mock.patch('tethys_services.models.PersistentStoreService.objects.get', return_value=True)
    def test_get_service_from_id_persistent(self, mock_get):
        self.assertEqual(install_commands.get_service_from_id(1).get('service_type'), 'persistent')
        mock_get.assert_called_with(id=1)

    @mock.patch('tethys_services.models.SpatialDatasetService.objects.get', return_value=True)
    def test_get_service_from_id_spatial(self, mock_get):
        self.assertEqual(install_commands.get_service_from_id(1).get('service_type'), 'spatial')
        mock_get.assert_called_with(id=1)

    @mock.patch('tethys_services.models.DatasetService.objects.get', return_value=True)
    def test_get_service_from_id_dataset(self, mock_get):
        self.assertEqual(install_commands.get_service_from_id(1).get('service_type'), 'dataset')
        mock_get.assert_called_with(id=1)

    @mock.patch('tethys_services.models.WebProcessingService.objects.get', return_value=True)
    def test_get_service_from_id_wps(self, mock_get):
        self.assertEqual(install_commands.get_service_from_id(1).get('service_type'), 'wps')
        mock_get.assert_called_with(id=1)

    @mock.patch('tethys_services.models.PersistentStoreService.objects.get', return_value=True)
    def test_get_service_from_name_persistent(self, mock_get):
        self.assertEqual(install_commands.get_service_from_name("nonexisting").get('service_type'), 'persistent')
        mock_get.assert_called_with(name='nonexisting')

    @mock.patch('tethys_services.models.SpatialDatasetService.objects.get', return_value=True)
    def test_get_service_from_name_spatial(self, mock_get):
        self.assertEqual(install_commands.get_service_from_name("nonexisting").get('service_type'), 'spatial')
        mock_get.assert_called_with(name='nonexisting')

    @mock.patch('tethys_services.models.DatasetService.objects.get', return_value=True)
    def test_get_service_from_name_dataset(self, mock_get):
        self.assertEqual(install_commands.get_service_from_name("nonexisting").get('service_type'), 'dataset')
        mock_get.assert_called_with(name='nonexisting')

    @mock.patch('tethys_services.models.WebProcessingService.objects.get', return_value=True)
    def test_get_service_from_name_wps(self, mock_get):
        self.assertEqual(install_commands.get_service_from_name("nonexisting").get('service_type'), 'wps')
        mock_get.assert_called_with(name='nonexisting')

    @mock.patch('tethys_apps.cli.init_commands.input')
    def test_get_interactive_input(self, mock_input):
        install_commands.get_interactive_input()
        mock_input.assert_called_with("")

    @mock.patch('tethys_apps.cli.init_commands.input')
    def test_get_service_name_input(self, mock_input):
        install_commands.get_service_name_input()
        mock_input.assert_called_with("")

    def test_parse_id_input(self):
        self.assertEqual(install_commands.parse_id_input("1,2"), (True, [1, 2]))
        self.assertEqual(install_commands.parse_id_input("3"), (True, [3]))
        self.assertEqual(install_commands.parse_id_input("werwr"), (False, ['werwr']))


class TestInstallServicesCommands(unittest.TestCase):
    def setUp(self):
        self.src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.root_app_path = os.path.join(self.src_dir, 'apps', 'tethysapp-test_app')

        from tethys_services.models import (PersistentStoreService, WebProcessingService)
        # Create test service
        test_service_name = "test_service_for_install"
        try:
            PersistentStoreService.objects.get(name=test_service_name)
        except Exception:
            new_service = PersistentStoreService(name=test_service_name, host='localhost',
                                                 port='1000', username='user', password='pass')
            new_service.save()

        test_service_name = "test_wps_for_install"

        try:
            WebProcessingService.objects.get(name=test_service_name)
        except Exception:
            new_service = WebProcessingService(
                name=test_service_name, endpoint='localhost', username='user', password='pass')
            new_service.save()

    def tearDown(self):

        from tethys_services.models import (PersistentStoreService, WebProcessingService)
        # Create test service
        test_service_name = "test_service_for_install"
        try:
            service = PersistentStoreService.objects.get(name=test_service_name)
            service.delete()
        except Exception:
            pass

        test_service_name = "test_wps_for_install"
        try:
            service = WebProcessingService.objects.get(name=test_service_name)
            service.delete()
        except Exception:
            pass

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    @mock.patch('tethys_apps.cli.init_commands.get_interactive_input', return_value='test_service_for_install')
    @mock.patch('tethys_apps.cli.init_commands.get_service_name_input', return_value='primary')
    @mock.patch('tethys_apps.cli.init_commands.link_service_to_app_setting')
    def test_interactive_run(self, mock_link, mock_input, mock_input_2, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        services_path = os.path.join(self.root_app_path, 'services-interactive.yml')

        args = mock.MagicMock(file=file_path, services_file=services_path)
        mock_exit.side_effect = SystemExit

        with @mock.patch('sys.stdout', FNULL):
            self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("Running Interactive Service Mode.", po_call_args[2][0][0])
        self.assertIn("Please enter the name of the service from your app.py", po_call_args[6][0][0])
        self.assertIn("Services Configuration Completed.", po_call_args[7][0][0])

        mock_link.assert_called_with('persistent', 'test_service_for_install', 'test_app', 'ps_database', 'primary')

        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    @mock.patch('tethys_apps.cli.init_commands.get_interactive_input', side_effect=KeyboardInterrupt)
    def test_interactive_run_interrupt(self, mock_input, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        services_path = os.path.join(self.root_app_path, 'services-interactive.yml')

        args = mock.MagicMock(file=file_path, services_file=services_path)
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("Running Interactive Service Mode.", po_call_args[2][0][0])
        self.assertIn("Install Command cancelled.", po_call_args[6][0][0])

        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    @mock.patch('tethys_apps.cli.init_commands.link_service_to_app_setting')
    def test_portal_run(self, mock_link, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        portal_config_file = os.path.join(self.root_app_path, '../../portal_config/portal_test.yml')

        args = mock.MagicMock(file=file_path, portal_file=portal_config_file, services_file="", force_services=False)
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list

        self.assertIn("Portal init file found...Processing...", po_call_args[2][0][0])
        mock_link.assert_called_with('persistent', 'test_service_for_install', 'test_app', 'ps_database', 'primary')
        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.link_service_to_app_setting')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_basic_service(self, mock_pretty_output, mock_link, mock_exit):

        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        services_path = os.path.join(self.root_app_path, 'services-basic.yml')
        args = mock.MagicMock(file=file_path, services_file="")

        try:
            import tethysapp.test_app  # noqa: F401
            # Do a sync to ensure that the application's custom setting has been added
            subprocess.call(['tethys', 'manage', 'syncdb'], stdout=FNULL, stderr=subprocess.STDOUT)
        except ImportError:
            install_commands.init_command(args)

        from tethys_services.models import PersistentStoreService
        # Create test service
        test_service_name = "test_persistent_install"
        try:
            PersistentStoreService.objects.get(name=test_service_name)
        except Exception:
            new_service = PersistentStoreService(name=test_service_name, host='localhost',
                                                 port='1000', username='user', password='pass')
            new_service.save()

        mock_exit.side_effect = SystemExit

        args = mock.MagicMock(file=file_path, services_file=services_path)

        self.assertRaises(SystemExit, install_commands.init_command, args)

        mock_link.assert_called_with('persistent', test_service_name, 'test_app', 'ps_database', 'temp_db')

        mock_exit.assert_called_with(0)


class TestInstallCommands(unittest.TestCase):
    def setUp(self):
        self.src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.root_app_path = os.path.join(self.src_dir, 'apps', 'tethysapp-test_app')
        pass

    def tearDown(self):
        pass

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_init_file_input_param_error(self, mock_pretty_output, mock_exit):
        args = mock.MagicMock(file='./dummypath/doesnotexisst/test.yml')

        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("No Install File found", po_call_args[0][0][0])
        mock_exit.assert_called_with(1)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_no_conda_input_file(self, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-no-dep.yml')
        args = mock.MagicMock(file=file_path)
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("No Conda options found. Does your app not have any dependencies?", po_call_args[0][0][0])
        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_skip_dep_input_file(self, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        args = mock.MagicMock(file=file_path, services_file="")
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("Skipping dependency installation, Skip option found.", po_call_args[0][0][0])
        self.assertIn("Running application install....", po_call_args[1][0][0])
        self.assertIn("No Services init file found. Skipping app service installation", po_call_args[2][0][0])

        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_post_command(self, mock_pretty_output, mock_exit):
        file_path = os.path.join(self.root_app_path, 'install-with-post.yml')
        args = mock.MagicMock(file=file_path, services_file="")
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("Running application install....", po_call_args[1][0][0])
        self.assertIn("No Services init file found. Skipping app service installation", po_call_args[2][0][0])
        self.assertIn("Running post installation tasks...", po_call_args[3][0][0])
        self.assertIn("Post Script Result: b'test\\n'", po_call_args[4][0][0])

        mock_exit.assert_called_with(0)

    @mock.patch('tethys_apps.cli.init_commands.exit')
    @mock.patch('tethys_apps.cli.init_commands.pretty_output')
    def test_install_clean(self, mock_pretty_output, mock_exit):

        try:
            import tethysapp.test_app  # noqa: F401
            # If import succeeds, we have an instance of the app. Clean it out
            subprocess.call(['tethys', 'uninstall', 'test_app', '-f'], stdout=FNULL, stderr=subprocess.STDOUT)
        except ImportError:
            pass

        file_path = os.path.join(self.root_app_path, 'install-skip-setup.yml')
        args = mock.MagicMock(file=file_path, services_file="")
        mock_exit.side_effect = SystemExit

        self.assertRaises(SystemExit, install_commands.init_command, args)

        po_call_args = mock_pretty_output().__enter__().write.call_args_list
        self.assertIn("Running application install....", po_call_args[1][0][0])

        try:
            import tethysapp.test_app  # noqa: F401, F811
        except ImportError:
            self.fail("We should be able to import tethys application")

        mock_exit.assert_called_with(0)
