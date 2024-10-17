import asyncio
import os
from aiohttp import web

from meross_iot.controller.mixins.electricity import ElectricityMixin
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
import logging

from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

EMAIL = os.environ.get('MEROSS_EMAIL')
PASSWORD = os.environ.get('MEROSS_PASSWORD')

# Define Prometheus metrics
power_gauge = Gauge('meross_device_power_watts', 'Power consumption in watts', ['device_name'])
voltage_gauge = Gauge('meross_device_voltage_volts', 'Voltage in volts', ['device_name'])
current_gauge = Gauge('meross_device_current_amperes', 'Current in amperes', ['device_name'])

async def collect_metrics():
    # Setup the HTTP client API from user-password
    http_api_client = await MerossHttpClient.async_from_user_password(email=EMAIL, password=PASSWORD, api_base_url="https://iotx-eu.meross.com")

    # Setup and start the device manager
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()

    # Retrieve all the devices that implement the electricity mixin
    await manager.async_device_discovery()
    devs = manager.find_devices(device_class=ElectricityMixin)

    for dev in devs:
        # Update device status
        await dev.async_update()

        # Read the electricity power/voltage/current
        instant_consumption = await dev.async_get_instant_metrics()
        power_gauge.labels(device_name=dev.name).set(instant_consumption.power)
        voltage_gauge.labels(device_name=dev.name).set(instant_consumption.voltage)
        current_gauge.labels(device_name=dev.name).set(instant_consumption.current)

    # Close the manager and logout from http_api
    manager.close()
    await http_api_client.async_logout()

async def metrics_handler(request):
    await collect_metrics()
    return web.Response(body=generate_latest(), content_type='text/plain', charset='utf-8')

async def init_app():
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    return app

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.WARNING)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=1400)
