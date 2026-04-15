import os
import environ

environ.Env.read_env(os.path.join(".env"))

env = environ.Env(
    DEBUG=(bool, False),
    PROJECT_ENV=(str, "prod"),
)
