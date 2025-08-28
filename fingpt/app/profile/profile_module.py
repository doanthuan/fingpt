from dependency_injector import containers, providers

from .profile_controller import ProfileController


class ProfileModule(containers.DeclarativeContainer):

    profile_ctrl: providers.Provider[ProfileController] = providers.Singleton(
        ProfileController,
    )
