# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from .fse_version import VERSION as __version__  # noqa: F401
from .hx711 import HX711

from mfrc522 import SimpleMFRC522

import flask

from flask import jsonify, request, make_response, Response

from octoprint.server.util.flask import restricted_access


try:
    import RPi.GPIO as GPIO
except (ModuleNotFoundError, RuntimeError):
    import Mock.GPIO as GPIO  # noqa: F401


# pylint: disable=too-many-ancestors
class FilamentInfoPlugin(octoprint.plugin.SettingsPlugin,
                          octoprint.plugin.AssetPlugin,
                          octoprint.plugin.TemplatePlugin,
                          octoprint.plugin.StartupPlugin,
                          octoprint.plugin.BlueprintPlugin):

    hx = None
    t = None
    t_rfid = None
    w_brutto = None
    w_netto = None
    w_tare = None
    w_raw = None
    reader = None
    rfid_id = None
    rfid_data = None
    filament_manufacturer = 'Unknown'
    filament_product = 'Unknown'
    filament_type = 'Unknown'
    filament_color = 'Unknown'
    filament_spool_weight = 'Unknown'
    
    @staticmethod
    def get_template_configs():
        return [
            dict(type="settings", custom_bindings=True)
        ]

    @staticmethod
    def get_settings_defaults():
        return dict(
            tare=8430152,
            reference_unit=-411,
            spool_weight=50,
            clockpin=21,
            datapin=20,
            lastknownweight=0,
            output_weight=0
        )
        

    @staticmethod
    def get_assets():
        return dict(
            js=["js/filament_info.js"],
            css=["css/filament_info.css"],
            less=["less/filament_info.less"]
        )

    def on_startup(self, host, port):  # pylint: disable=unused-argument
        self._logger.info("on startup wejscie")
        self.hx = HX711(20, 21)
        self.hx.set_reading_format("LSB", "MSB")
        self.hx.reset()
        self.hx.power_up()
        self.t = octoprint.util.RepeatedTimer(3.0, self.check_weight)
        self.t.start()
        
        self.reader = SimpleMFRC522()
        self.t_rfid = octoprint.util.RepeatedTimer(5.0, self.check_rfid)
        self.t_rfid.start()
        self._logger.info("on startup wyjscie")
        
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

    def check_rfid(self):
        self._logger.info("check_rfid wejscie")
        self.rfid_id, self.rfid_data = self.reader.read()
        y = self.rfid_data.rstrip()	
        x = y.split (', ')
        self.filament_manufacturer = x[0]
        self.filament_product = x[1]
        self.filament_type = x[2]
        self.filament_color = x[3]
        self.filament_spool_weight = x[4]      

        value = int(self.filament_spool_weight)

        self._settings.set(["spool_weight"], value)
        self._settings.save(False,True)        
       # text = "ID: %s\nText: %s" % (id,text)
        self._logger.info("Rfid read: %s, %s, %s, %s, %s" % (self.filament_manufacturer, self.filament_product, self.filament_type, self.filament_color, self.filament_spool_weight))
        
    def check_weight(self):
       # self._logger.info("check weight wejscie")
        self.hx.power_up()
        v = self.hx.read()
        self._plugin_manager.send_plugin_message(self._identifier, v)
        self.hx.power_down()
        
        self.w_raw = v
        
        self.w_brutto = round ((v - self._settings.get(["tare"])) / self._settings.get(["reference_unit"]))
        self.w_tare = int(self._settings.get(["spool_weight"]))
        self.w_netto = max(self.w_brutto - int(self._settings.get(["spool_weight"])), 0)
      #  self._logger.info("check weight wyjscie")
        

    # pylint: disable=line-too-long
    def get_update_information(self):
        # Define the configuration for your plugin to use with the
        # Software Update Plugin here.
        # See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            filament_info=dict(
                displayName="Filament Info Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="PrzMat",
                repo="Filament-Info",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/PrzMat/Filament-Info/releases/latest/download/Filament-Info.zip"  # noqa: E501
            )
        )


    @octoprint.plugin.BlueprintPlugin.route("/tare", methods=["POST"])
    @restricted_access
    def tare_post(self):
        self._settings.set(["tare"], self.w_raw)
        self._settings.save(False,True)
         
        return jsonify(reference_unit=self._settings.get(["reference_unit"]), tare=self._settings.get(["tare"]))  

    @octoprint.plugin.BlueprintPlugin.route("/calib", methods=["POST"])
    @restricted_access
    def calib_post(self):
        if "application/json" not in request.headers["Content-Type"]:
            return make_response("expected json", 400)
        try:
            data = request.json
        except BadRequest:
            return make_response("malformed request", 400)

        if 'known_weight' not in data:
            return make_response("missing known_weight attribute", 406)

        calib_data = data["known_weight"]
        data = round (self.w_raw - self._settings.get(["tare"]))
                
        value = data / calib_data
        
        self._settings.set(["reference_unit"], value)
        self._settings.save(False,True)
         
        #return make_response('', 204)  
        return jsonify(reference_unit=self._settings.get(["reference_unit"]), tare=self._settings.get(["tare"]))
 
    @octoprint.plugin.BlueprintPlugin.route("/calib", methods=["GET"])
    def calib_get(self):
        # This is a GET request and thus not subject to CSRF protection
        #return str(self.w_netto)
        return jsonify(reference_unit=self._settings.get(["reference_unit"]), tare=self._settings.get(["tare"]))
        
    @octoprint.plugin.BlueprintPlugin.route("/filament", methods=["PUT"])
    @restricted_access
    def filament_put(self):
        if "application/json" not in request.headers["Content-Type"]:
            return make_response("expected json", 400)
        try:
            data = request.json
        except BadRequest:
            return make_response("malformed request", 400)

        if 'spool_weight' not in data:
            return make_response("missing spool_weight attribute", 406)

        value = data["spool_weight"]

        self._settings.set(["spool_weight"], value)
        self._settings.save(False,True)
         
        return make_response('', 204)

    @octoprint.plugin.BlueprintPlugin.route("/filament", methods=["GET"])
    def filament_get(self):
        # This is a GET request and thus not subject to CSRF protection
        #return str(self.w_netto)
        return jsonify(manufacturer=self.filament_manufacturer, product=self.filament_product, type=self.filament_type, color=self.filament_color, filament_weight=self.w_netto, spool_weight=self.w_tare, total_weight=self.w_brutto)


__plugin_name__ = "Filament Info"  # pylint: disable=global-variable-undefined
__plugin_pythoncompat__ = ">=3,<4"  # pylint: disable=global-variable-undefined


# pylint: disable=global-variable-undefined
def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FilamentInfoPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin5.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
