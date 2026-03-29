"""AWS Lambda entry point using Mangum."""

from mangum import Mangum

from vindicara.api.app import create_app

app = create_app()
handler = Mangum(app, lifespan="off")
