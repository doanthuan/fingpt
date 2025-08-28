from dependency_injector import containers, providers

from app.command.command_controller import CommandController


class CommandModule(containers.DeclarativeContainer):
    command_ctrl: providers.Provider[CommandController] = providers.Singleton(
        CommandController,
    )
