from dependency_injector import containers, providers

from app.auth.auth_controller import AuthController

from .auth_service import AuthService


class AuthModule(containers.DeclarativeContainer):
    auth_srv: providers.Provider[AuthService] = providers.Singleton(
        AuthService,
    )

    auth_ctrl: providers.Provider[AuthController] = providers.Singleton(
        AuthController,
        auth_srv=auth_srv,
    )
