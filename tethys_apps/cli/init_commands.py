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

    print(config)

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


def runInteractiveServices():
    write_msg('Running Interactive Service Mode. Any configuration options in init.yml for services will be ignored...')

    # List existing services
    tempNS = Namespace()

    for conf in ['spatial', 'persistent', 'wps', 'dataset']:
        setattr(tempNS, conf, False)

    services_list_command(tempNS)

    try:
        write_msg(
            'Please enter the service ID to link one of the above listed service.')
        write_msg(
            'You may also enter a comma seperated list of service ids : (1,2).')
        write_msg(
            'Just hit return if you wish to skip this step and move on to creating your own services.')
        response = input("")
        if response != "":
                # Parse Response
            print("re")
        else:
            write_msg("Create new service....")

    except (KeyboardInterrupt, SystemExit):
        with pretty_output(FG_YELLOW) as p:
            p.write('\nInit Command cancelled.')
        exit(1)


def init_command(args):
    """
    Init Command
    """
    try:
        appName = None
        # Check if input config file exists. We Can't do anything without it
        file_path = args.file

        if file_path is None:
            file_path = './init.yml'

        if not path.exists(file_path):
            write_error(
                'No Init File found. Please ensure init.yml exists in the root of your app and run the command from that directory')

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

        # condaConfig = initOptions['conda']
        # # Add all channels listed in the file.
        # if "channels" in condaConfig:
        #     channels = condaConfig['channels']
        #     if channels and len(channels) > 0:
        #         for channel in channels:
        #             [resp, err, code] = conda_run(
        #                 Commands.CONFIG, "--env --add channels {}".format(channel), use_exception_handler=True)

        # # Install all Dependencies

        # if "dependencies" in condaConfig:
        #     dependencies = condaConfig['dependencies']
        #     depList = " ".join(dependencies)
        #     with pretty_output(FG_BLUE) as p:
        #         p.write('Installing Dependencies.....')
        #     [resp, err, code] = conda_run(
        #         Commands.INSTALL, depList, use_exception_handler=False, stdout=None, stderr=None)
        #     if code != 0:
        #         with pretty_output(FG_RED) as p:
        #             p.write(
        #                 'Warning: Dependencies installation ran into an error. Please try again or a manual install')

        # Setup any services that need to be setup

        if "tethys" in initOptions:
            tethysConfig = initOptions['tethys']
            if "services" in tethysConfig:
                services = tethysConfig['services']
                if "interactive" in services:
                    if services["interactive"]:
                        runInteractiveServices()
                else:
                    if services and len(services) > 0:
                        for service in services:
                            if services[service] is not None:
                                create_and_link(
                                    service, services[service], appName)

        exit(0)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            if e:
                p.write(e)
            p.write('An unexpected error occurred. Please try again.')
        exit(1)
