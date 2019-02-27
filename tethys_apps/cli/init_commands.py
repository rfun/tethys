from os import path
from tethys_apps.cli.cli_colors import pretty_output, FG_RED, FG_BLUE
from conda.cli.python_api import run_command as conda_run, Commands
import yaml
# @TODO : Probably have better error messages/prompts


def init_command(args):
    """
    Init Command
    """
    try:

        # Check if input config file exists. We Can't do anything without it
        file_path = args.file

        if file_path is None:
            file_path = './init.yml'

        if not path.exists(file_path):
            with pretty_output(FG_RED) as p:
                p.write(
                    'No Init File found. Please ensure init.yml exists in the root of your app and run the command from that directory')
            exit(1)

        try:
            with open(file_path) as f:
                initOptions = yaml.safe_load(f)

        except Exception as e:
            with pretty_output(FG_RED) as p:
                p.write(e)
                p.write(
                    'An unexpected error occurred reading the file. Please try again.')
                exit(1)

        if "conda" not in initOptions:
            with pretty_output(FG_RED) as p:
                p.write(
                    'No Conda options found. Does your app not have any dependencies? ')
            exit(1)

        condaConfig = initOptions['conda']
        # Add all channels listed in the file.
        if "channels" in condaConfig:
            channels = condaConfig['channels']
            if channels and len(channels) > 0:
                for channel in channels:
                    [resp, err, code] = conda_run(
                        Commands.CONFIG, "--env --add channels {}".format(channel), use_exception_handler=True)

        # Install all Dependencies

        if "dependencies" in condaConfig:
            dependencies = condaConfig['dependencies']
            depList = " ".join(dependencies)
            with pretty_output(FG_BLUE) as p:
                p.write('Installing Dependencies.....')
            [resp, err, code] = conda_run(
                Commands.INSTALL, depList, use_exception_handler=False, stdout=None, stderr=None)
            if code not 0:
                with pretty_output(FG_RED) as p:
                    p.write(
                        'Warning: Dependencies installation ran into an error. Please try again or a manual install')

        exit(0)

    except Exception as e:
        with pretty_output(FG_RED) as p:
            p.write(e)
            p.write('An unexpected error occurred. Please try again.')
        exit(1)
