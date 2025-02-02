import logging

import voluptuous as vol
import asyncio

from homeassistant import bootstrap
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import *
from .Token import Token
from .Vehicle import Vehicle
from .KiaUvoApi import KiaUvoApi
from datetime import datetime, timezone

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry):
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    async def async_handle_force_update(call):
        vehicle = hass.data[DOMAIN][DATA_VEHICLE_INSTANCE]
        await vehicle.force_update()

    async def async_handle_update(call):
        vehicle = hass.data[DOMAIN][DATA_VEHICLE_INSTANCE]
        await vehicle.update()

    async def async_handle_start_climate(call):
        vehicle = hass.data[DOMAIN][DATA_VEHICLE_INSTANCE]
        await vehicle.start_climate()

    async def async_handle_stop_climate(call):
        vehicle = hass.data[DOMAIN][DATA_VEHICLE_INSTANCE]
        await vehicle.stop_climate()

    hass.services.async_register(DOMAIN, "force_update", async_handle_force_update)
    hass.services.async_register(DOMAIN, "update", async_handle_update)
    hass.services.async_register(DOMAIN, "start_climate", async_handle_start_climate)
    hass.services.async_register(DOMAIN, "stop_climate", async_handle_stop_climate)

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    _LOGGER.debug(f"{DOMAIN} - async_setup_entry started - {config_entry}")
    email = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    credentials = config_entry.data.get(CONF_STORED_CREDENTIALS)
    unit_of_measurement = DISTANCE_UNITS[config_entry.options.get(CONF_UNIT_OF_MEASUREMENT, DEFAULT_DISTANCE_UNIT)]
    no_force_scan_hour_start = config_entry.options.get(CONF_NO_FORCE_SCAN_HOUR_START, DEFAULT_NO_FORCE_SCAN_HOUR_START)
    no_force_scan_hour_finish = config_entry.options.get(CONF_NO_FORCE_SCAN_HOUR_FINISH, DEFAULT_NO_FORCE_SCAN_HOUR_FINISH)
    scan_interval = timedelta(minutes=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    force_scan_interval = timedelta(minutes=config_entry.options.get(CONF_FORCE_SCAN_INTERVAL, DEFAULT_FORCE_SCAN_INTERVAL))

    kia_uvo_api = KiaUvoApi(email, password)
    vehicle = Vehicle(hass, config_entry, Token(credentials), kia_uvo_api, unit_of_measurement)

    data = {
        DATA_VEHICLE_INSTANCE: vehicle,
        DATA_VEHICLE_LISTENER: None,
        DATA_FORCED_VEHICLE_LISTENER: None,
        DATA_CONFIG_UPDATE_LISTENER: None
    }

    async def refresh_config_entry():
        is_token_updated = await vehicle.refresh_token()
        if is_token_updated:
            new_data = config_entry.data.copy()
            new_data[CONF_STORED_CREDENTIALS] = vars(vehicle.token)
            hass.config_entries.async_update_entry(config_entry, data = new_data, options = config_entry.options)

    async def update(event_time_utc: datetime):
        await refresh_config_entry()
        await vehicle.refresh_token()
        event_time_local = event_time_utc.astimezone(TIME_ZONE_EUROPE)
        _LOGGER.debug(f"{DOMAIN} - Decide to make a force call current hour {event_time_local.hour} blackout start {no_force_scan_hour_start} blackout finish {no_force_scan_hour_finish} force scan interval {force_scan_interval}")

        await vehicle.update()
        if (event_time_local.hour < no_force_scan_hour_start and event_time_local.hour >= no_force_scan_hour_finish):
            if datetime.now(TIME_ZONE_EUROPE) - vehicle.last_updated > force_scan_interval:
                try:
                    await vehicle.force_update()
                except Exception as ex:
                    _LOGGER.error(f"{DOMAIN} - Exception in force update : %s", str(ex))
        else:
            _LOGGER.debug(f"{DOMAIN} - We are in silent hour zone / no automatic force updates {event_time_local}")
        

    await update(dt_util.utcnow())

    for platform in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, platform))

    data[DATA_VEHICLE_LISTENER] = async_track_time_interval(hass, update, scan_interval)
    data[DATA_CONFIG_UPDATE_LISTENER] = config_entry.add_update_listener(async_update_options)
    hass.data[DOMAIN] = data

    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        config_update_listener = hass.data[DOMAIN][DATA_CONFIG_UPDATE_LISTENER]
        config_update_listener()
        vehicle_topic_listener = hass.data[DOMAIN][DATA_VEHICLE_LISTENER]
        vehicle_topic_listener()
        hass.data[DOMAIN] = None

    return unload_ok
