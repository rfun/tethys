import os
import webbrowser
import subprocess
from tethys_apps.cli.manage_commands import get_manage_path, run_process
from tethys_apps.utilities import get_tethys_src_dir
# from tethys_apps.models import TethysExtension, TethysApp

TETHYS_SRC_DIRECTORY = get_tethys_src_dir()
FNULL = open(os.devnull, 'w')


def test_command(args):
    args.manage = False
    # Get the path to manage.py
    manage_path = get_manage_path(args)
    tests_path = os.path.join(TETHYS_SRC_DIRECTORY, 'tests')

    # Define the process to be run
    primary_process = ['python', manage_path, 'test']

    try:
        import tethysapp.test_app  # noqa: F401
    except Exception:

        print("Test App not found. Installing.....")
        setup_path = os.path.join(
            tests_path, 'apps', 'tethysapp-test_app')
        subprocess.call(['python', 'setup.py', 'develop'],
                        stdout=FNULL, stderr=subprocess.STDOUT, cwd=setup_path)

    try:
        import tethysext.test_extension  # noqa: F401
    except Exception:

        print("Test Extension not found. Installing.....")
        setup_path = os.path.join(
            tests_path, 'extensions', 'tethysext-test_extension')
        subprocess.call(['python', 'setup.py', 'develop'],
                        stdout=FNULL, stderr=subprocess.STDOUT, cwd=setup_path)

    # Tag to later check if tests are being run on a specific app or extension
    app_package_tag = 'tethys_apps.tethysapp.'
    extension_package_tag = 'tethysext.'

    if args.coverage or args.coverage_html:
        os.environ['TETHYS_TEST_DIR'] = tests_path
        if args.file and app_package_tag in args.file:
            app_package_parts = args.file.split(app_package_tag)
            app_name = app_package_parts[1].split('.')[0]
            core_app_package = '{}{}'.format(app_package_tag, app_name)
            app_package = 'tethysapp.{}'.format(app_name)
            config_opt = '--source={},{}'.format(core_app_package, app_package)
        elif args.file and extension_package_tag in args.file:
            extension_package_parts = args.file.split(extension_package_tag)
            extension_name = extension_package_parts[1].split('.')[0]
            core_extension_package = '{}{}'.format(
                extension_package_tag, extension_name)
            extension_package = 'tethysext.{}'.format(extension_name)
            config_opt = '--source={},{}'.format(
                core_extension_package, extension_package)
        else:
            config_opt = '--rcfile={0}'.format(
                os.path.join(tests_path, 'coverage.cfg'))
        primary_process = ['coverage', 'run', config_opt, manage_path, 'test']

    if args.file:
        primary_process.append(args.file)
    elif args.unit:
        primary_process.append(os.path.join(tests_path, 'unit_tests'))
    elif args.gui:
        primary_process.append(os.path.join(tests_path, 'gui_tests'))

    primary_process.append('--keepdb')
    primary_process.append('--failfast')

    test_status = run_process(primary_process)

    if args.coverage:
        if args.file and (app_package_tag in args.file or extension_package_tag in args.file):
            run_process(['coverage', 'report'])
        else:
            run_process(['coverage', 'report', config_opt])

    if args.coverage_html:
        report_dirname = 'coverage_html_report'
        index_fname = 'index.html'

        if args.file and (app_package_tag in args.file or extension_package_tag in args.file):
            run_process(
                ['coverage', 'html', '--directory={0}'.format(os.path.join(tests_path, report_dirname))])
        else:
            run_process(['coverage', 'html', config_opt])

        try:
            status = run_process(['open', os.path.join(
                tests_path, report_dirname, index_fname)])
            if status != 0:
                raise Exception
        except Exception:
            webbrowser.open_new_tab(os.path.join(
                tests_path, report_dirname, index_fname))

    # Removing Test App

    # try:
    #     print("Uninstalling Test App.....")
    #     subprocess.call(['tethys', 'uninstall', 'test_app', '-f'])
    # except Exception as e:
    #     print(e)
    #     print("Test App wasn't installed. Nothing to cleanup")

    # try:
    #     print("Uninstalling Test Extention.....")
    #     subprocess.call(['tethys', 'uninstall', 'test_extension', '-ef'])
    # except Exception as e:
    #     print(e)
    #     print("Test Extension wasn't installed. Nothing to cleanup")

    exit(test_status)
