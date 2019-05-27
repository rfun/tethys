import yaml
import os

from subprocess import (call, Popen, PIPE, STDOUT)
from argparse import Namespace
from conda.cli.python_api import run_command as conda_run, Commands
from django.core.exceptions import ObjectDoesNotExist
from tethys_apps.cli.cli_colors import pretty_output, FG_RED, FG_BLUE, FG_YELLOW
from tethys_apps.cli.services_commands import services_list_command

from tethys_apps.utilities import link_service_to_app_setting

FNULL = open(os.devnull, 'w')

serviceLinkParam = {
    'spatial': 'ds_spatial',
    "dataset": 'ds_dataset',
    "persistent": 'ps_database',
    'wps': 'wps'
}


def write_error(msg):
    with pretty_output(FG_RED) as p:
        p.write(msg)
    exit(1)


def write_msg(msg):
    with pretty_output(FG_YELLOW) as p:
        p.write(msg)


def get_service_from_id(id):

    from tethys_services.models import (SpatialDatasetService, PersistentStoreService,
                                        DatasetService, WebProcessingService)

    try:
        persistent_entries = PersistentStoreService.objects.get(id=id)  # noqa: F841
        return {"service_type": "persistent",
                "linkParam": serviceLinkParam['persistent']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = SpatialDatasetService.objects.get(id=id)  # noqa: F841
        return {"service_type": "spatial",
                "linkParam": serviceLinkParam['spatial']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = DatasetService.objects.get(id=id)  # noqa: F841
        return {"service_type": "dataset",
                "linkParam": serviceLinkParam['dataset']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = WebProcessingService.objects.get(id=id)  # noqa: F841
        return {"service_type": "wps",
                "linkParam": serviceLinkParam['persistent']}
    except ObjectDoesNotExist:
        pass

    return False


def get_service_from_name(name):

    from tethys_services.models import (SpatialDatasetService, PersistentStoreService,
                                        DatasetService, WebProcessingService)

    try:
        persistent_entries = PersistentStoreService.objects.get(name=name)  # noqa: F841
        return {"service_type": "persistent",
                "linkParam": serviceLinkParam['persistent']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = SpatialDatasetService.objects.get(name=name)  # noqa: F841
        return {"service_type": "spatial",
                "linkParam": serviceLinkParam['spatial']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = DatasetService.objects.get(name=name)  # noqa: F841
        return {"service_type": "dataset",
                "linkParam": serviceLinkParam['dataset']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = WebProcessingService.objects.get(name=name)  # noqa: F841
        return {"service_type": "wps",
                "linkParam": serviceLinkParam['wps']}
    except ObjectDoesNotExist:
        pass

    return False


# Pulling this function out so I can mock this for inputs to the interactive mode

def get_interactive_input():
    return input("")


def get_service_name_input():
    return input("")


def parse_id_input(inputResponse):
    id_search = False

    try:
        ids = inputResponse.split(',')
        ids = list(map(lambda x: int(x), ids))

        id_search = True
    except ValueError:
        ids = [inputResponse]
        pass

    return id_search, ids


def run_interactive_services(app_name):
    write_msg('Running Interactive Service Mode. '
              'Any configuration options in install.yml for services will be ignored...')

    # List existing services
    tempNS = Namespace()

    for conf in ['spatial', 'persistent', 'wps', 'dataset']:
        setattr(tempNS, conf, False)

    services_list_command(tempNS)

    write_msg('Please enter the service ID/Name to link one of the above listed service.')
    write_msg('You may also enter a comma seperated list of service ids : (1,2).')
    write_msg('Just hit return if you wish to skip this step and move on to creating your own services.')

    valid = False
    while not valid:
        try:
            response = get_interactive_input()
            if response != "":
                # Parse Response
                id_search, ids = parse_id_input(response)

                for service_id in ids:
                    if id_search:
                        service = get_service_from_id(service_id)
                    else:
                        service = get_service_from_name(service_id)
                    if service:
                        # Ask for app setting name:
                        write_msg(
                            'Please enter the name of the service from your app.py eg: "catalog_db")')
                        setting_name = get_service_name_input()
                        link_service_to_app_setting(service['service_type'],
                                                    service_id,
                                                    app_name,
                                                    service['linkParam'],
                                                    setting_name)

                valid = True

            else:
                write_msg(
                    "Please run 'tethys services create -h' to create services via the command line.")
                valid = True

        except (KeyboardInterrupt, SystemExit):
            with pretty_output(FG_YELLOW) as p:
                p.write('\nInstall Command cancelled.')
            exit(0)


def find_and_link(service_type, setting_name, service_id, app_name):

    service = get_service_from_name(service_id)
    if service:
        link_service_to_app_setting(service['service_type'],
                                    service_id,
                                    app_name,
                                    service['linkParam'],
                                    setting_name)
    else:
        with pretty_output(FG_RED) as p:
            p.write(
                'Warning: Could not find service of type: {} with the name/id: {}'.format(service_type, service_id))


def run_portal_init(service_models, file_path, app_name):

    if file_path is None:
        file_path = './portal.yml'

    if not os.path.exists(file_path):
        write_msg("No Portal Services file found. Moving to look for local app level services.yml...")
        return False

    try:
        write_msg("Portal init file found...Processing...")
        with open(file_path) as f:
            portal_options = yaml.safe_load(f)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write('An unexpected error occurred reading the file. Please try again.')
            return False

    if "apps" in portal_options and app_name in portal_options['apps'] and 'services' in portal_options['apps'][app_name]:
        services = portal_options['apps'][app_name]['services']
        if services and len(services) > 0:
            for service_type in services:
                if services[service_type] is not None:
                    current_services = services[service_type]
                    for service_setting_name in current_services:
                        find_and_link(service_type, service_setting_name,
                                      current_services[service_setting_name], app_name)
        else:
            write_msg("No app configuration found for app: {} in portal config file. ".format(app_name))

    else:
        write_msg("No apps configuration found in portal config file. ".format(app_name))

    return True


def install_dependencies(conda_config):
    # Add all channels listed in the file.
    if "channels" in conda_config and conda_config['channels'] and len(conda_config['channels']) > 0:
        channels = conda_config['channels']
        for channel in channels:
            [resp, err, code] = conda_run(
                Commands.CONFIG, "--prepend channels {}".format(channel), use_exception_handler=True)

    # Install all Dependencies

    if "dependencies" in conda_config and conda_config['dependencies'] and len(conda_config['dependencies']) > 0:
        dependencies = conda_config['dependencies']
        with pretty_output(FG_BLUE) as p:
            p.write('Installing Dependencies.....')
        [resp, err, code] = conda_run(
            Commands.INSTALL, *dependencies, use_exception_handler=False, stdout=None, stderr=None)
        if code != 0:
            with pretty_output(FG_RED) as p:
                p.write('Warning: Dependencies installation ran into an error. Please try again or a manual install')


def run_services(services_config, file_path, app_name, serviceFileInput):

    if serviceFileInput is None:
        file_path = './services.yml'
    else:
        file_path = serviceFileInput

    if not os.path.exists(file_path):
        write_msg("No Services init file found. Skipping app service installation")
        return

    try:
        with open(file_path) as f:
            init_options = yaml.safe_load(f)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write('An unexpected error occurred reading the file. Please try again.')
            exit(1)

    # Setup any services that need to be setup
    services = init_options
    interactive_mode = False
    skip = False

    if "skip" in services:
        skip = services['skip']
        del services['skip']
    if "interactive" in services:
        interactive_mode = services['interactive']
        del services['interactive']

    if not skip:
        if interactive_mode:
            run_interactive_services(app_name)
        else:
            if services and len(services) > 0:
                if services['version']:
                    del services['version']
                for service_type in services:
                    if services[service_type] is not None:
                        current_services = services[service_type]
                        for service_setting_name in current_services:
                            find_and_link(service_type, service_setting_name,
                                          current_services[service_setting_name], app_name)
        write_msg("Services Configuration Completed.")
    else:
        write_msg(
            "Skipping services configuration, Skip option found.")


def init_command(args):
    """
    Init Command
    """

    # Have to import within function or else install partial on a system fails
    from tethys_services.models import (
        SpatialDatasetService, DatasetService, PersistentStoreService, WebProcessingService)

    service_models = {
        'spatial': SpatialDatasetService,
        "dataset": DatasetService,
        "persistent": PersistentStoreService,
        'wps': WebProcessingService
    }

    app_name = None
    # Check if input config file exists. We Can't do anything without it
    file_path = args.file

    if file_path is None:
        file_path = './install.yml'

    if not os.path.exists(file_path):
        write_error(
            'No Install File found. Please ensure install.yml exists or check the file path entered.')

    try:
        with open(file_path) as f:
            init_options = yaml.safe_load(f)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write(
                'An unexpected error occurred reading the file. Please try again.')
            exit(1)

    if "name" in init_options:
        app_name = init_options['name']

    if "conda" not in init_options:
        with pretty_output(FG_BLUE) as p:
            p.write(
                'No Conda options found. Does your app not have any dependencies?')
        exit(0)

    conda_config = init_options['conda']

    skip = False
    if "skip" in conda_config:
        skip = conda_config['skip']
        del conda_config['skip']

    if skip:
        write_msg("Skipping dependency installation, Skip option found.")
    else:
        install_dependencies(conda_config)

    # Run Setup.py
    write_msg("Running application install....")

    call(['python', 'setup.py', 'develop'], stdout=FNULL, stderr=STDOUT)
    call(['tethys', 'manage', 'sync'])

    # Run Portal Level Config if present
    if args.force_services:
        run_services(service_models, file_path, app_name, args.services_file)
    else:
        portal_result = run_portal_init(service_models, args.portal_file, app_name)
        if not portal_result:
            run_services(service_models, file_path, app_name, args.services_file)

    # Check to see if any extra scripts need to be run

    if "post" in init_options and init_options["post"] and len(init_options["post"]) > 0:
        write_msg("Running post installation tasks...")
        for post in init_options["post"]:
            path_to_post = os.path.join(os.path.dirname(os.path.realpath(file_path)), post)
            # Attempting to run processes.
            process = Popen(path_to_post, shell=True, stdout=PIPE)
            stdout = process.communicate()[0]
            write_msg("Post Script Result: {}".format(stdout))
    exit(0)
