from os import path
from tethys_apps.cli.cli_colors import pretty_output, FG_RED, FG_BLUE, FG_YELLOW
from tethys_apps.cli.services_commands import (services_create_persistent_command, services_create_spatial_command,
                                               services_create_dataset_command, services_create_wps_command,
                                               services_list_command
                                               )

from tethys_services.models import (
    SpatialDatasetService, DatasetService, PersistentStoreService, WebProcessingService)

from tethys_apps.models import TethysApp

from tethys_apps.utilities import link_service_to_app_setting

from django.core.exceptions import ObjectDoesNotExist
from argparse import Namespace
from conda.cli.python_api import run_command as conda_run, Commands
import yaml
from subprocess import (call, Popen, PIPE)
# @TODO : Probably have better error messages/prompts

services = {
    'spatial': {
        'create': services_create_spatial_command,
        'model': SpatialDatasetService,
        'linkParam': 'ds_spatial'
    },
    "dataset": {
        'create': services_create_dataset_command,
        'model': DatasetService,
        'linkParam': 'ds_dataset'
    },
    "persistent": {
        'create': services_create_persistent_command,
        'model': PersistentStoreService,
        'linkParam': 'ps_database'
    },
    'wps': {
        'create': services_create_wps_command,
        'model': WebProcessingService,
        'linkParam': 'wps'
    }
}


def write_error(msg):
    with pretty_output(FG_RED) as p:
        p.write(msg)
    exit(1)


def write_msg(msg):
    with pretty_output(FG_YELLOW) as p:
        p.write(msg)


def create_and_link(serviceKey, config, appName=""):

    service = services.get(serviceKey)
    newService = None

    if appName:
        config['name'] = "{0}-{1}".format(appName, config['name'])

    try:
        try:
            serviceKey = int(serviceKey)
            newService = service['model'].objects.get(pk=serviceKey)
        except ValueError:
            newService = service['model'].objects.get(name=config['name'])
            with pretty_output(FG_BLUE) as p:
                p.write(
                    'Service with name "{0}" already exists. Skipping add.'.format(config['name']))
    except ObjectDoesNotExist:
        if not service:
            write_error(
                'Invalid Service Type : {0}. \n Please choose from the following options: [{1}]'.format(
                    serviceKey, ', '.join(services.keys())))

        serviceMethod = service['create']
        tempNS = Namespace()

        for conf in config.keys():
            setattr(tempNS, conf, config[conf])

        newService = serviceMethod(tempNS)

    link_service_to_app_setting(
        serviceKey, config['name'], appName, service['linkParam'], config['setting-name'])


def getServiceFromID(id):

    from tethys_services.models import SpatialDatasetService, PersistentStoreService, DatasetService, WebProcessingService

    try:
        persistent_entries = PersistentStoreService.objects.get(id=id)
        return {"service_type": "persistent",
                "linkParam": services['persistent']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = SpatialDatasetService.objects.get(id=id)
        return {"service_type": "spatial",
                "linkParam": services['spatial']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = DatasetService.objects.get(id=id)
        return {"service_type": "dataset",
                "linkParam": services['dataset']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = WebProcessingService.objects.get(id=id)
        return {"service_type": "wps",
                "linkParam": services['persistent']['linkParam']}
    except ObjectDoesNotExist:
        pass

    return False


def getServiceFromName(name):

    from tethys_services.models import SpatialDatasetService, PersistentStoreService, DatasetService, WebProcessingService

    try:
        persistent_entries = PersistentStoreService.objects.get(name=name)
        return {"service_type": "persistent",
                "linkParam": services['persistent']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = SpatialDatasetService.objects.get(name=name)
        return {"service_type": "spatial",
                "linkParam": services['spatial']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = DatasetService.objects.get(name=name)
        return {"service_type": "dataset",
                "linkParam": services['dataset']['linkParam']}
    except ObjectDoesNotExist:
        pass

    try:
        entries = WebProcessingService.objects.get(name=name)
        return {"service_type": "wps",
                "linkParam": services['wps']['linkParam']}
    except ObjectDoesNotExist:
        pass

    return False


def runInteractiveServices(appName):
    write_msg('Running Interactive Service Mode. Any configuration options in install.yml for services will be ignored...')

    # List existing services
    tempNS = Namespace()

    for conf in ['spatial', 'persistent', 'wps', 'dataset']:
        setattr(tempNS, conf, False)

    services_list_command(tempNS)

    write_msg(
        'Please enter the service ID to link one of the above listed service.')
    write_msg(
        'You may also enter a comma seperated list of service ids : (1,2).')
    write_msg(
        'Just hit return if you wish to skip this step and move on to creating your own services.')

    valid = False

    while not valid:
        try:
            response = input("")
            if response != "":
                # Parse Response
                try:
                    ids = int(response.replace(',', ''))
                    if not isinstance(ids, list):
                        ids = [ids]
                    for service_id in ids:
                        service = getServiceFromID(service_id)
                        if service:
                            # Ask for app setting name:
                            write_msg(
                                'Please enter the name of the service from your app.py eg: "catalog_db")')
                            setting_name = input("")
                            link_service_to_app_setting(service['service_type'],
                                                        service_id,
                                                        appName,
                                                        service['linkParam'],
                                                        setting_name)

                    valid = True
                except ValueError:
                    with pretty_output(FG_RED) as p:
                        p.write("Invalid Input...Please try again.")
            else:
                write_msg(
                    "Please run 'tethys services create -h' to create services via the command line.")
                valid = True

        except (KeyboardInterrupt, SystemExit):
            with pretty_output(FG_YELLOW) as p:
                p.write('\nInstall Command cancelled.')
            exit(1)


def find_and_link(serviceType, settingName, serviceID, appName):

    service = getServiceFromName(serviceID)
    if service:
        link_service_to_app_setting(service['service_type'],
                                    serviceID,
                                    appName,
                                    service['linkParam'],
                                    settingName)
    else:
        with pretty_output(FG_RED) as p:
            p.write(
                'Warning: Could not find service of type: {} with the name/id: {}'.format(serviceType, serviceID))


def run_portal_init(filePath, appName):

    if filePath is None:
        filePath = './portal.yml'

    if not path.exists(filePath):
        write_msg(
            """No Portal Services file found. Moving to look for local app level services.yml...""")
        return False

    try:
        write_msg("Portal init file found...Processing...")
        with open(filePath) as f:
            portal_options = yaml.safe_load(f)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write(
                'An unexpected error occurred reading the file. Please try again.')
            return False

    if "apps" in portal_options and appName in portal_options['apps'] and 'services' in portal_options['apps'][appName]:
        services = portal_options['apps'][appName]['services']
        if services and len(services) > 0:
            for serviceType in services:
                if services[serviceType] is not None:
                    current_services = services[serviceType]
                    for service_setting_name in current_services:
                        find_and_link(serviceType, service_setting_name,
                                      current_services[service_setting_name], appName)
        else:
            write_msg(
                "No app configuration found for app: {} in portal config file. ".format(appName))

    else:
        write_msg(
            "No apps configuration found in portal config file. ".format(appName))

    return True


def install_dependencies(condaConfig):
     # Add all channels listed in the file.
    if "channels" in condaConfig and condaConfig['channels'] and len(condaConfig['channels']) > 0:
        channels = condaConfig['channels']
        for channel in channels:
            [resp, err, code] = conda_run(
                Commands.CONFIG, "--prepend channels {}".format(channel), use_exception_handler=True)

    # Install all Dependencies

    if "dependencies" in condaConfig and condaConfig['dependencies'] and len(condaConfig['dependencies']) > 0:
        dependencies = condaConfig['dependencies']
        with pretty_output(FG_BLUE) as p:
            p.write('Installing Dependencies.....')
        [resp, err, code] = conda_run(
            Commands.INSTALL, *dependencies, use_exception_handler=False, stdout=None, stderr=None)
        if code != 0:
            with pretty_output(FG_RED) as p:
                p.write(
                    'Warning: Dependencies installation ran into an error. Please try again or a manual install')


def run_services(filePath, appName):

    filePath = './services.yml'

    if not path.exists(filePath):
        write_error(
            """No Services init file found. Skipping app service installation""")

    try:
        with open(filePath) as f:
            initOptions = yaml.safe_load(f)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write(
                'An unexpected error occurred reading the file. Please try again.')
            exit(1)

    # Setup any services that need to be setup
    services = initOptions
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
            runInteractiveServices(appName)
        else:
            if services and len(services) > 0:
                if services['version']:
                    del services['version']
                for serviceType in services:
                    if services[serviceType] is not None:
                        current_services = services[serviceType]
                        for service_setting_name in current_services:
                            find_and_link(serviceType, service_setting_name,
                                          current_services[service_setting_name], appName)
        write_msg("Services Configuration Completed.")
    else:
        write_msg(
            "Skipping services configuration, Skip option found.")


def init_command(args):
    """
    Init Command
    """
    try:
        appName = None
        # Check if input config file exists. We Can't do anything without it
        file_path = args.file

        if file_path is None:
            file_path = './install.yml'

        if not path.exists(file_path):
            write_error(
                'No Install File found. Please ensure install.yml exists in the root of your app and run the command from that directory')

        try:
            with open(file_path) as f:
                initOptions = yaml.safe_load(f)

        except Exception as e:
            with pretty_output(FG_RED) as p:
                p.write(e)
                p.write(
                    'An unexpected error occurred reading the file. Please try again.')
                exit(1)

        if "name" in initOptions:
            appName = initOptions['name']

        if "conda" not in initOptions:
            with pretty_output(FG_BLUE) as p:
                p.write(
                    'No Conda options found. Does your app not have any dependencies? ')
            exit(0)

        condaConfig = initOptions['conda']

        skip = False
        if "skip" in condaConfig:
            skip = condaConfig['skip']
            del condaConfig['skip']

        if skip:
            write_msg("Skipping dependency installation, Skip option found.")
        else:
            install_dependencies(condaConfig)

        # Run Setup.py

        program_name = "python setup.py develop"
        write_msg("Running application install....")
        call(['python', 'setup.py', 'develop'])
        call(['tethys', 'manage', 'sync'])

        # Run Portal Level Config if present
        if args.force_services:
            run_services(file_path, appName)
        else:
            portal_result = run_portal_init(args.portal_file, appName)
            if not portal_result:
                run_services(file_path, appName)

        # Check to see if any extra scripts need to be run

        if "post" in initOptions and initOptions["post"] and len(initOptions["post"]) > 0:
            write_msg("Running post installation tasks...")
            for post in initOptions["post"]:
                # Attempting to run processes.
                process = Popen(
                    post, shell=True, stdout=PIPE)
                stdout = process.communicate()[0]
                print(stdout)
        exit(0)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            if e:
                p.write(e)
            p.write('An unexpected error occurred. Please try again.')
        exit(1)
