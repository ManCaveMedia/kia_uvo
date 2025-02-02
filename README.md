I have baked a custom integration for EU Kia Uvo, this will be working for new account types. Thanks for your hard work [@wcomartin](https://github.com/wcomartin/kiauvo). This project was mostly inspired by his [home assistant integration](https://github.com/wcomartin/kia_uvo)

Warning ahead; this is pre-alpha phase, please do not expect something fully functional, I will improve the integration by time.

You can install this either manually copying files or using HACS. Configuration can be done on UI, you need to enter your username and password, (I know, translations are missing!). 

- it will only fetch values for the first car, I am not sure if there are people outside using Kia Uvo with multiple cars :)
- update - It will fetch the cached information every 30 minutes from Kia Servers. **Now Configurable**
- force update - It will ask your car for the latest data every 4 hours. **Now Configurable**
- It will not force update between 10PM to 6AM. I am trying to be cautios here. **Now Configurable**
- By default, distance unit is kilometers, you need to configure the integration if you want to switch to miles.

Supported entities;
- Air Conditioner Status, Defroster Status
- Heated Rear Window, Heated Steering Wheel
- Car Battery Level (12v), EV Battery Level
- Tire Pressure Warnings (individual and all)
- Charge Status and Plugged In Status
- Low Fuel Light Status (for PHEV and IC)
- Doors, Trunk and Hood Open/Close Status
- Locking and Unlocking
- Engine Status
- Location (over GPS)
- Odometer, EV Range (for PHEV and EV), Fuel Range (for PHEV and IC), Total Range (for PHEV and EV)
- Latest Update
- Configurable distance units, cache update interval, force update interval, blackout start and finish hours

Supported service;
- force_update: this will make a call to your vehicle to get its latest data, do not overuse this!
- update: get latest **cached** vehicle data
- start_climate: I am not able to test this as I own an PHEV but looking for volunteers to help on this
- stop_climate: I am not able to test this as I own an PHEV but looking for volunteers to help on this

I have posted an example screenshot from my own car.

![Device Details](https://github.com/fuatakgun/kia_uvo/blob/master/Device%20Details.PNG?raw=true)
![Device Details](https://github.com/fuatakgun/kia_uvo/blob/master/Configuration.PNG?raw=true)

**Troubleshooting**
If you receive an error while trying to login, please go through these steps;
1. As of now, integration only supports EU region, so if you are outside, you are more than welcome to create an issue and become a test user for changes to expand coverage.
2. If you are in EU, please log out from UVO app and login again. While logging in, if your account was created in legacy UVO servers, they will be migrated to new Kia servers. Related Issue: https://github.com/fuatakgun/kia_uvo/issues/22
3. If you have migrated recently, you might need to wait one day to try again. Related Issue: https://community.home-assistant.io/t/kia-uvo-integration-pre-alpha/297927/12?u=fuatakgun
4. As a last resort, please double check your account credentials.
5. You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, update your `configuration.yaml` like this, we can get more information in Configuration -> Logs page
```
logger:
  default: warning
  logs:
    custom_components.kia_uvo: debug
```
