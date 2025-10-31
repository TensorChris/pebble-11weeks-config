var battery;
var config;

var CHARGING_MASK =           0x80;
var LEVEL_MASK =              0x7f;
var BATTERY_API_UNSUPPORTED = 0x70;

var PKEY_CONFIG = "pebble-watch-11weeks-config";
var DEFAULT_CONFIG = 0;

var getBatteryStateInt = function () {
  'use strict';
  var state = 0;
  console.log("battery is: " + battery);
  if (battery) {
    state = Math.round(battery.level * 100);
    if (battery.charging) {
      state |= CHARGING_MASK;
    }
    console.log('got battery state: ' + state);
  } else {
    state = BATTERY_API_UNSUPPORTED;
    console.log('battery API unsupported.');
  }
  return state;
};

var sendBatteryState = function () {
  'use strict';
  var dict = {
    "KEY_PHONE_BATTERY": getBatteryStateInt()
  };
  Pebble.sendAppMessage(dict, function() {
    console.log('Message sent successfully: ' + JSON.stringify(dict));
  }, function(e) {
    console.log('Message failed: ' + JSON.stringify(e));
  });
};

var handleBattery = function () {
  'use strict';
  if (battery) {
    battery.addEventListener('chargingchange', sendBatteryState);
    battery.addEventListener('levelchange', sendBatteryState);
  }
  sendBatteryState();
};

var initBattery = function () {
  'use strict';
  battery = navigator.battery || navigator.webkitBattery || navigator.mozBattery;
  console.log("set battery: " + battery);
  if (navigator.getBattery) {
    console.log("battery API exists.");
    navigator.getBattery().then(function (b) {
      battery = b;
      console.log("set battery in then(): " + b);
      handleBattery();
    });
  } else {
    handleBattery();
  }
};

var sendConfig = function () {
  'use strict';
  var dict = {
    'KEY_CONFIG_VALUE': config
  };
  Pebble.sendAppMessage(dict, function() {
    console.log('Message sent successfully: ' + JSON.stringify(dict));
  }, function(e) {
    console.log('Message failed: ' + JSON.stringify(e));
  });
};

Pebble.addEventListener('ready', function (e) {
  'use strict';
  // Load saved config from localStorage
  var savedConfig = localStorage.getItem(PKEY_CONFIG);
  if (savedConfig !== null) {
    config = parseInt(savedConfig);
  } else {
    config = DEFAULT_CONFIG;
  }
  // Send config to watch
  sendConfig();
  initBattery();
});

Pebble.addEventListener('showConfiguration', function(e) {
  'use strict';
  // Embedded config page as Data-URI
  var configHtml = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>11 Weeks Config</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:sans-serif;background:#eee;padding:15px}h1{text-align:center;color:#666;font-size:1.3em;margin-bottom:20px}.section{background:#fff;border-radius:8px;margin-bottom:15px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.section-header{padding:10px 15px;background:#f5f5f5;border-bottom:1px solid #ddd;font-weight:bold;color:#666;font-size:0.9em;text-transform:uppercase}.option{padding:15px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}.option:last-child{border-bottom:none}.option-label{flex:1;font-size:1em;color:#333}.toggle-container{position:relative;width:50px;height:26px}.toggle-input{display:none}.toggle-switch{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background-color:#ccc;transition:0.3s;border-radius:13px}.toggle-switch:before{position:absolute;content:"";height:20px;width:20px;left:3px;bottom:3px;background-color:white;transition:0.3s;border-radius:50%}.toggle-input:checked + .toggle-switch{background-color:#ff4700}.toggle-input:checked + .toggle-switch:before{transform:translateX(24px)}.btn{display:block;width:80%;max-width:300px;margin:20px auto;padding:15px;background:#ff4700;color:white;border:none;border-radius:8px;font-size:1.1em;font-weight:bold;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,0.2)}.btn:active{transform:translateY(1px)}.info{padding:10px 15px;font-size:0.85em;color:#666;line-height:1.4}</style></head><body><h1>11 Weeks Configuration</h1><div class="section"><div class="section-header">Display Options</div><div class="option"><span class="option-label">Seconds (refresh per sec)</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="sec-layer" checked><label class="toggle-switch" for="sec-layer"></label></div></div><div class="option"><span class="option-label">Outline Frame</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="frame-layer" checked><label class="toggle-switch" for="frame-layer"></label></div></div><div class="option"><span class="option-label">Pebble Battery</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="battery-layer" checked><label class="toggle-switch" for="battery-layer"></label></div></div><div class="option"><span class="option-label">Phone Battery & Bluetooth</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="bt-phone-layer" checked><label class="toggle-switch" for="bt-phone-layer"></label></div></div><div class="option"><span class="option-label">Week starts on Monday</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="week-start-monday" checked><label class="toggle-switch" for="week-start-monday"></label></div></div><div class="option"><span class="option-label">Quiet Time Indicator</span><div class="toggle-container"><input type="checkbox" class="toggle-input" id="quiet-time-layer" checked><label class="toggle-switch" for="quiet-time-layer"></label></div></div><div class="info">Note: Seconds and outline frame increase battery usage.</div></div><button class="btn" id="save-btn">SAVE</button><script>var INJECTED_CONFIG=null;var keys={\'sec-layer\':1,\'frame-layer\':2,\'battery-layer\':4,\'bt-phone-layer\':8,\'week-start-monday\':16,\'quiet-time-layer\':32};function getConfigFlags(){var config=0;for(var key in keys){var ctrl=document.getElementById(key);if(!ctrl.checked){config|=keys[key];}}return{\'config\':config};}(function(){var configValue=INJECTED_CONFIG;if(configValue!==null){console.log(\'Loading config: \'+configValue);for(var key in keys){var ctrl=document.getElementById(key);ctrl.checked=!(configValue&keys[key]);}}})();document.getElementById(\'save-btn\').addEventListener(\'click\',function(){console.log(\'Save clicked\');var result=getConfigFlags();console.log(\'Returning config: \'+JSON.stringify(result));document.location=\'pebblejs://close#\'+encodeURIComponent(JSON.stringify(result));});</script></body></html>';

  // Inject the current config value into the HTML
  var currentConfig = (config !== undefined && config !== null) ? config : 0;
  console.log('Opening config page with config: ' + currentConfig);
  configHtml = configHtml.replace('var INJECTED_CONFIG=null;', 'var INJECTED_CONFIG=' + currentConfig + ';');

  var url = 'data:text/html;charset=utf-8,' + encodeURIComponent(configHtml);
  Pebble.openURL(url);
});

Pebble.addEventListener('webviewclosed', function(e) {
  // Decode the user's preferences
  var configData = JSON.parse(decodeURIComponent(e.response));
  config = configData.config;
  // Save config to localStorage
  localStorage.setItem(PKEY_CONFIG, config);
  sendConfig();
});