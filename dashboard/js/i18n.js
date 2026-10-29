// Translations (es-ES by default, en kept) and Intl based date/time formatting in the configured time zone.
(function () {
  'use strict';
  var App = window.App;

  var DICT = {
    es: {
      nav_chores: 'Tareas', nav_cameras: 'Cámaras', ch_shared: 'Casa', cal_week_n: 'Semana {n}', cal_wk: 'Sem.', ch_see_all: 'Ver todas', undo: 'Deshacer', ch_done_toast: 'Hecho: {name}', ch_all_done: '¡Todo hecho!', ch_none: 'Hoy no hay tareas.', ch_none2: 'Disfruta del descanso.', ch_today: 'tareas de hoy',
      nav_music: 'Música', mu_kicker: 'Spotify', mu_lists: 'Mis listas', mu_search: 'Buscar', mu_search_ph: 'Canción, artista o lista…', mu_speakers: 'Altavoz', mu_nothing: 'No suena nada', mu_nothing2: 'Elige una lista o busca una canción.',
      mu_off: 'Spotify no está conectado.', mu_off2: 'Conéctalo desde el panel de administración.', mu_nodev: 'No hay ningún altavoz activo.', mu_nodev2: 'Abre Spotify en uno de tus altavoces y aparecerá aquí.',
      mu_empty: 'Sin resultados.', mu_err: 'No se pudo hablar con Spotify.', mu_track: 'Canción', mu_album: 'Álbum', mu_playlist: 'Lista',
      ch_overdue: 'Pendiente de antes', ch_once: 'Tarea puntual',
      al_alarm: 'Alarma', al_notice: 'Aviso', al_snooze: 'Posponer {n} min', al_stop: 'Parar', al_close: 'Cerrar',
      chime_say: function (v) {
        var h = v.h % 12 || 12, q = v.m >= 30 ? ' y media' : '';
        return (h === 1 ? 'Es la una' : 'Son las ' + h) + q;
      },
      nav_menu: 'Menú', mn_kicker: 'Semanal', mn_week: 'Semana', mn_today: 'HOY', mn_back: 'Esta semana', mn_prev: 'Semana anterior', mn_next: 'Semana siguiente', mn_none: 'Aún no hay menú.', mn_none2: 'Añádelo desde el panel de administración.', mn_week_empty: 'Esta semana no tiene comidas.', meal_breakfast: 'Desayuno', meal_midmorning: 'Media mañana', meal_lunch: 'Comida', meal_snack: 'Merienda', meal_dinner: 'Cena',
      cam_kicker: 'En directo', cam_none: 'No hay cámaras configuradas.', cam_none2: 'Añádelas desde el panel de administración.', cam_reload: 'Recargar', cam_error: 'No se puede mostrar la cámara.',
      g_covers: 'Persianas y cortinas', cover_open: 'Abierta', cover_closed: 'Cerrada', cover_opening: 'Abriendo', cover_closing: 'Cerrando', cover_up: 'Subir', cover_down: 'Bajar', cover_stop: 'Parar',
      nav_home: 'Hoy', nav_calendar: 'Calendario', nav_photos: 'Fotos', nav_house: 'Casa', nav_shopping: 'Compra', nav_settings: 'Ajustes',
      today: 'Hoy', now: 'Ahora', prev: 'Anterior', next: 'Siguiente', back: 'Atrás', cancel: 'Cancelar', save: 'Guardar', delete: 'Eliminar',
      dismiss: 'Descartar', details: 'Mostrar detalles', more: 'más', never: 'Nunca', on: 'Encendido', off: 'Apagado', unavailable: 'No disponible',
      live: 'En directo', stale: 'último estado conocido', home: 'En casa', away: 'Fuera', ran: 'Ejecutado: {name}',
      all_day: 'Todo el día', events: 'eventos', free: 'Libre', everyone: 'Todos', no_people: 'Aún no hay personas configuradas',
      rest_of_day: 'Resto del día', rest_of_day_l: 'el resto del día', nothing_else: 'Nada más por hoy.', enjoy_quiet: 'Disfruta de la calma.',
      tomorrow_starts: 'Mañana empieza con {title} a las {time}', next_up: 'A continuación', hero_later: 'Después', more_n: '+{n} más', more_events: '{n} eventos más',
      overlapping: 'Coinciden', day_of: 'Día {n} de {m}', n_days: '{n} días',
      cal_3day: '3 días', cal_week: 'Semana', cal_month: 'Mes', cal_next7: 'Próximos 7 días', cal_empty: 'No hay nada en el calendario.', cal_empty2: 'Un día tranquilo.',
      notice_calendar: 'Calendario sin sincronizar: {name}',
      items_to_get: 'por comprar', lights_on: 'luces encendidas', inside: 'en casa', ha_live: 'Home Assistant conectado', ha_down: 'Sin conexión con Home Assistant',
      ha_not_configured: 'Home Assistant sin configurar',
      on_this_day: 'Tal día como hoy', years_ago_today: function (v) { return 'Hace ' + v.n + (v.n === 1 ? ' año' : ' años') + ', tal día como hoy'; },
      years_ago: function (v) { return 'Hace ' + v.n + (v.n === 1 ? ' año' : ' años'); }, this_year: 'Este año',
      photos_none: 'Aún no hay fotos. Súbelas desde el panel de administración.',
      ly_auto: 'Auto', ly_cover: 'Completa', ly_pair: 'Pareja', ly_collage: 'Collage', ly_polaroid: 'Polaroid',
      first_up: 'Lo primero {when}', nothing_early: 'Nada temprano mañana',
      wx_none: 'Sin datos del tiempo', wx_hi_lo: 'Máx. {hi}° · mín. {lo}°', wx_sun: 'Despejado', wx_moon: 'Despejado', wx_partly: 'Parcialmente nublado',
      wx_cloud: 'Nublado', wx_rain: 'Lluvia', wx_rain_until: 'Lluvia hasta las {h}', wx_rain_from: 'Lluvia a partir de las {h}', wx_umbrella: 'Lleva paraguas',
      wx_jacket_rain: 'Chaqueta y paraguas por si acaso', wx_clear_cool: 'Despejado y fresco', wx_dry: 'Seco', wx_jacket: 'Mejor con chaqueta', wx_light: 'Ropa ligera',
      hvac_off: 'Apagado', hvac_heat: 'Calor', hvac_cool: 'Frío', hvac_heat_cool: 'Auto', hvac_auto: 'Auto', hvac_dry: 'Deshumidificar', hvac_fan_only: 'Ventilador',
      hvac_heating: 'Calentando', hvac_cooling: 'Enfriando', hvac_idle: 'En espera', hvac_drying: 'Deshumidificando', hvac_fan: 'Ventilando',
      bin_on_open: 'Abierto', bin_off_open: 'Cerrado', bin_on_motion: 'Movimiento', bin_off_motion: 'Sin movimiento', bin_on_generic: 'Activo', bin_off_generic: 'Inactivo',
      g_climate: 'Clima', g_lights: 'Luces', g_switches: 'Enchufes e interruptores', g_scenes: 'Escenas y scripts', g_sensors: 'Sensores',
      house_kicker: 'Home Assistant', house_hint: 'Elige las entidades que se muestran desde el panel de administración.',
      house_last_state: 'Sin conexión: se muestra el último estado conocido y los controles están desactivados.',
      shop_kicker: 'Lista de la compra', shop_placeholder: 'Añadir un producto…', shop_to_get: 'Por comprar', shop_pending: 'Pendiente', shop_done: 'Comprado',
      shop_empty: 'La lista está vacía.', shop_empty2: 'Añade lo que falte en casa.', shop_hint: 'Toca un producto para marcarlo como comprado.',
      shop_again: 'Volver a añadir', shop_reopen: 'Volver a pendiente', shop_complete: 'Marcar como comprado', shop_edit: 'Editar',
      shop_clear: 'Quitar comprados ({n})', shop_clear_q: '¿Quitar {n} productos comprados?', shop_add_label: 'Añadir', shop_add_named: 'Añadir «{name}»',
      shop_added: 'Añadido: {name}', shop_already: '{name} ya estaba en la lista', shop_checked: 'Comprado: {name}',
      shop_offline: 'Sin conexión: los cambios se enviarán al reconectar.', shop_provider_down: 'El servicio de la lista no responde: se muestra la última copia.',
      shop_pending_sync: '{n} cambios pendientes de enviar',
      setup_title: 'Conectar con Home HQ', setup_step1: 'Paso 1 de 2', setup_step2: 'Paso 2 de 2', setup_help: 'Introduce la dirección del servidor Home HQ de tu red o elígela de la lista.',
      setup_connect: 'Conectar', setup_rate: 'Demasiados intentos. Espera un momento.', setup_unreachable: 'No se puede conectar con el servidor. Revisa la dirección y la red.', setup_need_url: 'Introduce la dirección del servidor.', setup_code_title: 'Aprueba este marco', setup_code_help: 'Abre el panel de administración, ve a «Marcos» y aprueba la solicitud con este código.',
      setup_expires: 'caduca en {s}', setup_rejected: 'El administrador ha rechazado la solicitud.', setup_expired: 'La solicitud ha caducado. Vuelve a intentarlo.', setup_revoked: 'Este marco ha sido desvinculado. Vuelve a emparejarlo.',
      st_kicker: 'Estado del marco', st_connection: 'Conexión', st_server: 'Servidor', st_state: 'Estado', st_last_sync: 'Última sincronización', st_frame: 'Marco', st_ha: 'Home Assistant',
      st_clock_skew: 'El reloj del marco difiere {m} min del servidor.', st_sync_now: 'Sincronizar ahora', st_unpair_hold: 'Mantén pulsado para desvincular', st_keep_holding: 'Sigue pulsando para desvincular',
      st_screen: 'Pantalla', st_brightness: 'Brillo', st_night: 'Modo noche', st_sleep: 'Reposo', st_cap: 'Apagado de pantalla', st_sleep_now: 'Reposar ahora',
      st_activity: 'Actividad (sensor de luz)', st_sensor: 'Sensor', st_lux: 'Luz', st_baseline: 'Referencia', st_activity_now: 'Actividad', st_sens_set: 'Sensibilidad: {v}',
      st_activity_note: 'Detecta cambios de luz, no personas: es una estimación aproximada de actividad.', st_recording: 'Grabando una calibración del sensor.', st_waiting: 'Esperando muestras…',
      up_title: 'Actualización de la aplicación', up_installed: 'Instalada', up_available: 'Publicada', up_current: 'Home HQ está al día',
      up_found: 'Hay una versión nueva', up_off: 'El administrador ha desactivado las actualizaciones', up_check: 'Buscar actualizaciones',
      up_check_failed: 'No se pudo consultar al servidor', up_download_install: 'Descargar e instalar', up_install_now: 'Instalar ahora', up_retry: 'Reintentar',
      up_downloading: 'Descargando… {n}%', up_ready: 'Descargada y verificada. Pulsa Instalar ahora y confirma en el diálogo de Android',
      up_installing: 'Abriendo el instalador de Android: confirma para terminar', up_error: 'No se pudo actualizar: {m}',
      up_toast: 'Hay una versión nueva de Home HQ ({v}). Ajustes → Actualización',
      st_about: 'Acerca de', st_app: 'Aplicación', st_device: 'Dispositivo', st_language: 'Idioma y zona horaria', st_android: 'Android',
      bm_automatic: 'automático', bm_manual: 'manual', bm_always_on: 'siempre encendida', so_never: 'nunca se apaga', so_black: 'pantalla negra', so_off: 'apagada',
      sens_low: 'Baja', sens_medium: 'Media', sens_high: 'Alta', ago_s: 'hace {n} s', ago_m: 'hace {n} min', ago_h: 'hace {n} h',
 no_backend: 'Sin conexión con Home HQ', house_no_entities: 'No hay entidades seleccionadas.', house_not_configured: 'Home Assistant no está configurado.',
      ha_offline_toast: 'Sin conexión: no se ha podido enviar la orden.', ha_error_toast: 'Home Assistant no ha aceptado la orden.',
      st_online: 'Conectado', st_offline: 'Sin conexión', st_ha_off: 'Desactivado', st_active: 'Actividad detectada', st_quiet: 'Sin actividad',
      st_no_sensor: 'Este dispositivo no tiene sensor de luz.', st_no_native: 'Solo disponible en la aplicación del marco.',
      shop_synced_ha: 'Sincronizada con Home Assistant', shop_synced_local: 'Lista local', shop_on_list: 'Ya en la lista',
      identify_toast: 'Este marco es «{name}»'
    },
    en: {
      nav_chores: 'Chores', nav_cameras: 'Cameras', ch_shared: 'Household', cal_week_n: 'Week {n}', cal_wk: 'Wk', ch_see_all: 'See all', undo: 'Undo', ch_done_toast: 'Done: {name}', ch_all_done: 'All done!', ch_none: 'No chores today.', ch_none2: 'Enjoy the break.', ch_today: 'chores today',
      nav_music: 'Music', mu_kicker: 'Spotify', mu_lists: 'My playlists', mu_search: 'Search', mu_search_ph: 'Song, artist or playlist…', mu_speakers: 'Speaker', mu_nothing: 'Nothing is playing', mu_nothing2: 'Pick a playlist or search for a song.',
      mu_off: 'Spotify is not connected.', mu_off2: 'Connect it from the admin panel.', mu_nodev: 'No speaker is active.', mu_nodev2: 'Open Spotify on one of your speakers and it will show up here.',
      mu_empty: 'No results.', mu_err: 'Could not reach Spotify.', mu_track: 'Song', mu_album: 'Album', mu_playlist: 'Playlist',
      ch_overdue: 'Overdue', ch_once: 'One-off',
      al_alarm: 'Alarm', al_notice: 'Notice', al_snooze: 'Snooze {n} min', al_stop: 'Stop', al_close: 'Close',
      chime_say: function (v) {
        var h = v.h % 12 || 12;
        return v.m >= 30 ? "It's half past " + h : "It's " + h + " o'clock";
      },
      nav_menu: 'Menu', mn_kicker: 'Weekly', mn_week: 'Week', mn_today: 'TODAY', mn_back: 'This week', mn_prev: 'Previous week', mn_next: 'Next week', mn_none: 'No menu yet.', mn_none2: 'Add it from the admin panel.', mn_week_empty: 'This week has no meals.', meal_breakfast: 'Breakfast', meal_midmorning: 'Mid-morning', meal_lunch: 'Lunch', meal_snack: 'Snack', meal_dinner: 'Dinner',
      cam_kicker: 'Live', cam_none: 'No cameras configured.', cam_none2: 'Add them from the admin panel.', cam_reload: 'Reload', cam_error: 'The camera cannot be shown.',
      g_covers: 'Blinds and curtains', cover_open: 'Open', cover_closed: 'Closed', cover_opening: 'Opening', cover_closing: 'Closing', cover_up: 'Raise', cover_down: 'Lower', cover_stop: 'Stop',
      nav_home: 'Today', nav_calendar: 'Calendar', nav_photos: 'Photos', nav_house: 'Home', nav_shopping: 'Shopping', nav_settings: 'Settings',
      today: 'Today', now: 'Now', prev: 'Previous', next: 'Next', back: 'Back', cancel: 'Cancel', save: 'Save', delete: 'Delete',
      dismiss: 'Dismiss', details: 'Show details', more: 'more', never: 'Never', on: 'On', off: 'Off', unavailable: 'Unavailable',
      live: 'Live', stale: 'last known state', home: 'Home', away: 'Away', ran: 'Ran {name}',
      all_day: 'All day', events: 'events', free: 'Free', everyone: 'Everyone', no_people: 'No people configured yet',
      rest_of_day: 'Rest of the day', rest_of_day_l: 'the rest of the day', nothing_else: 'Nothing else today.', enjoy_quiet: 'Enjoy the quiet.',
      tomorrow_starts: 'Tomorrow starts with {title} at {time}', next_up: 'Next up', hero_later: 'Later', more_n: '+{n} more', more_events: '{n} more events',
      overlapping: 'Overlapping', day_of: 'Day {n} of {m}', n_days: '{n} days',
      cal_3day: '3 Day', cal_week: 'Week', cal_month: 'Month', cal_next7: 'Next 7 days', cal_empty: 'Nothing on the calendar.', cal_empty2: 'A rare, quiet day.',
      notice_calendar: 'Calendar out of sync: {name}',
      items_to_get: 'to get', lights_on: 'lights on', inside: 'inside', ha_live: 'Home Assistant connected', ha_down: 'Home Assistant offline',
      ha_not_configured: 'Home Assistant not configured',
      on_this_day: 'On this day', years_ago_today: function (v) { return v.n + (v.n === 1 ? ' year' : ' years') + ' ago today'; },
      years_ago: function (v) { return v.n + (v.n === 1 ? ' year ago' : ' years ago'); }, this_year: 'This year',
      photos_none: 'No photos yet. Upload some from the admin panel.',
      ly_auto: 'Auto', ly_cover: 'Cover', ly_pair: 'Pair', ly_collage: 'Collage', ly_polaroid: 'Polaroid',
      first_up: 'First up {when}', nothing_early: 'Nothing early tomorrow',
      wx_none: 'No weather data', wx_hi_lo: 'H {hi}° · L {lo}°', wx_sun: 'Clear', wx_moon: 'Clear', wx_partly: 'Partly cloudy',
      wx_cloud: 'Cloudy', wx_rain: 'Rain', wx_rain_until: 'Rain until {h}', wx_rain_from: 'Rain from {h}', wx_umbrella: 'Take an umbrella',
      wx_jacket_rain: 'Jacket and umbrella, just in case', wx_clear_cool: 'Clear and cool', wx_dry: 'Dry', wx_jacket: 'Better with a jacket', wx_light: 'Light clothes',
      hvac_off: 'Off', hvac_heat: 'Heat', hvac_cool: 'Cool', hvac_heat_cool: 'Auto', hvac_auto: 'Auto', hvac_dry: 'Dry', hvac_fan_only: 'Fan',
      hvac_heating: 'Heating', hvac_cooling: 'Cooling', hvac_idle: 'Idle', hvac_drying: 'Drying', hvac_fan: 'Fan on',
      bin_on_open: 'Open', bin_off_open: 'Closed', bin_on_motion: 'Motion', bin_off_motion: 'Clear', bin_on_generic: 'Active', bin_off_generic: 'Inactive',
      g_climate: 'Climate', g_lights: 'Lights', g_switches: 'Plugs and switches', g_scenes: 'Scenes and scripts', g_sensors: 'Sensors',
      house_kicker: 'Home Assistant', house_hint: 'Choose which entities appear from the admin panel.',
      house_last_state: 'Offline: showing the last known state, controls are disabled.',
      shop_kicker: 'Shopping list', shop_placeholder: 'Add an item…', shop_to_get: 'To get', shop_pending: 'Pending', shop_done: 'Bought',
      shop_empty: 'The list is empty.', shop_empty2: 'Add whatever is missing at home.', shop_hint: 'Tap an item to mark it as bought.',
      shop_again: 'Add again', shop_reopen: 'Back to pending', shop_complete: 'Mark as bought', shop_edit: 'Edit',
      shop_clear: 'Clear bought ({n})', shop_clear_q: 'Remove {n} bought items?', shop_add_label: 'Add', shop_add_named: 'Add “{name}”',
      shop_added: 'Added {name}', shop_already: '{name} was already on the list', shop_checked: 'Bought {name}',
      shop_offline: 'Offline: changes will be sent when the connection returns.', shop_provider_down: 'The list service is not responding: showing the last copy.',
      shop_pending_sync: '{n} changes waiting to sync',
      setup_title: 'Connect to Home HQ', setup_step1: 'Step 1 of 2', setup_step2: 'Step 2 of 2', setup_help: 'Enter the address of the Home HQ server on your network, or pick it from the list.',
      setup_connect: 'Connect', setup_rate: 'Too many attempts. Wait a moment.', setup_unreachable: 'Cannot reach the server. Check the address and the network.', setup_need_url: 'Enter the server address.', setup_code_title: 'Approve this frame', setup_code_help: 'Open the admin panel, go to “Frames” and approve the request with this code.',
      setup_expires: 'expires in {s}', setup_rejected: 'The administrator rejected the request.', setup_expired: 'The request expired. Try again.', setup_revoked: 'This frame was unlinked. Pair it again.',
      st_kicker: 'Frame status', st_connection: 'Connection', st_server: 'Server', st_state: 'State', st_last_sync: 'Last sync', st_frame: 'Frame', st_ha: 'Home Assistant',
      st_clock_skew: 'The frame clock differs {m} min from the server.', st_sync_now: 'Sync now', st_unpair_hold: 'Press and hold to unlink', st_keep_holding: 'Keep holding to unlink',
      st_screen: 'Screen', st_brightness: 'Brightness', st_night: 'Night mode', st_sleep: 'Sleep', st_cap: 'Screen off', st_sleep_now: 'Sleep now',
      st_activity: 'Activity (light sensor)', st_sensor: 'Sensor', st_lux: 'Light', st_baseline: 'Baseline', st_activity_now: 'Activity', st_sens_set: 'Sensitivity: {v}',
      st_activity_note: 'It detects light changes, not people: a rough estimate of activity.', st_recording: 'Recording a sensor calibration.', st_waiting: 'Waiting for samples…',
      up_title: 'App update', up_installed: 'Installed', up_available: 'Published', up_current: 'Home HQ is up to date',
      up_found: 'A new version is available', up_off: 'The administrator has turned updates off', up_check: 'Check for updates',
      up_check_failed: 'Could not reach the server', up_download_install: 'Download and install', up_install_now: 'Install now', up_retry: 'Try again',
      up_downloading: 'Downloading… {n}%', up_ready: 'Downloaded and verified. Tap Install now and confirm in the Android dialog',
      up_installing: 'Opening the Android installer: confirm to finish', up_error: 'The update failed: {m}',
      up_toast: 'A new Home HQ version is available ({v}). Settings → Update',
      st_about: 'About', st_app: 'App', st_device: 'Device', st_language: 'Language and time zone', st_android: 'Android',
      bm_automatic: 'automatic', bm_manual: 'manual', bm_always_on: 'always on', so_never: 'never off', so_black: 'black screen', so_off: 'off',
      sens_low: 'Low', sens_medium: 'Medium', sens_high: 'High', ago_s: '{n} s ago', ago_m: '{n} min ago', ago_h: '{n} h ago',
 no_backend: 'No connection to Home HQ', house_no_entities: 'No entities selected.', house_not_configured: 'Home Assistant is not configured.',
      ha_offline_toast: 'Offline: the command could not be sent.', ha_error_toast: 'Home Assistant did not accept the command.',
      st_online: 'Connected', st_offline: 'Offline', st_ha_off: 'Disabled', st_active: 'Activity detected', st_quiet: 'No activity',
      st_no_sensor: 'This device has no light sensor.', st_no_native: 'Only available in the frame app.',
      shop_synced_ha: 'Synced with Home Assistant', shop_synced_local: 'Local list', shop_on_list: 'Already on the list',
      identify_toast: 'This frame is “{name}”'
    }
  };
  App.DICT = DICT;

  App.locale = 'es-ES';
  App.tz = 'Europe/Madrid';

  function lang() { return App.locale === 'en' ? 'en' : 'es'; }

  App.t = function (key, vars) {
    var v = DICT[lang()][key];
    if (v == null) v = DICT.en[key];
    if (v == null) return key;
    if (typeof v === 'function') return v(vars || {});
    if (!vars) return v;
    return v.replace(/\{(\w+)\}/g, function (m, k) { return vars[k] != null ? vars[k] : m; });
  };

  App.i18nApply = function (root) {
    Array.prototype.forEach.call((root || document).querySelectorAll('[data-t]'), function (el) { el.textContent = App.t(el.getAttribute('data-t')); });
    document.documentElement.lang = lang();
  };

  // ------------------------------------------------------------ formatting
  var F = {}, wallFmt = null;

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function mk(opts) { return new Intl.DateTimeFormat(App.locale === 'en' ? 'en-US' : 'es-ES', opts); }

  App.initFormat = function () {
    var tzOk = true;
    try { wallFmt = new Intl.DateTimeFormat('en-GB', { timeZone: App.tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
    catch (e) { tzOk = false; wallFmt = null; }
    if (!tzOk) App.tz = 'Europe/Madrid';
    var h12 = App.locale === 'en';
    F.time = mk({ hour: 'numeric', minute: '2-digit', hour12: h12 });
    F.hour = mk(h12 ? { hour: 'numeric', hour12: true } : { hour: '2-digit', minute: '2-digit', hour12: false });
    F.weekday = mk({ weekday: 'long' });
    F.weekdayShort = mk({ weekday: 'short' });
    F.month = mk({ month: 'long' });
    F.monthYear = mk({ month: 'long', year: 'numeric' });
    F.dayMonth = mk({ day: 'numeric', month: 'long' });
    F.dayMonthShort = mk({ day: 'numeric', month: 'short' });
    F.monthShort = mk({ month: 'short' });
    F.dateLong = mk({ weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    F.rtf = typeof Intl.RelativeTimeFormat === 'function' ? new Intl.RelativeTimeFormat(h12 ? 'en-US' : 'es-ES', { numeric: 'auto' }) : null;
    App.i18nApply();
    if (App.emit) App.emit('locale');
    if (App.rerender) App.rerender();
  };

  // A Date whose local fields hold the wall-clock time in the configured zone, so no view depends on the frame's own zone.
  App.wallNow = function () {
    var now = new Date();
    if (!wallFmt) return now;
    var o = {};
    wallFmt.formatToParts(now).forEach(function (p) { o[p.type] = p.value; });
    return new Date(+o.year, +o.month - 1, +o.day, +o.hour, +o.minute, +o.second);
  };

  var fmt = App.fmt = {
    time: function (d, withAmpm) {
      var s = F.time.format(d);
      if (App.locale === 'en' && withAmpm === false) return s.replace(/\s?[AP]M$/i, '');
      return s;
    },
    ampm: function (d) { return App.locale === 'en' ? (d.getHours() < 12 ? 'AM' : 'PM') : ''; },
    hour: function (d) { return F.hour.format(d); },
    hourLabel: function (h) {
      if (App.locale === 'en') return h === 12 ? 'Noon' : (h % 12 || 12) + (h < 12 ? ' AM' : ' PM');
      return ('0' + h).slice(-2) + ':00';
    },
    day: function (d) { return cap(F.weekday.format(d)); },
    dayShort: function (d) { return cap(F.weekdayShort.format(d).replace('.', '')); },
    month: function (d) { return cap(F.month.format(d)); },
    monthShort: function (d) { return F.monthShort.format(d).replace('.', ''); },
    monthYear: function (d) { return cap(F.monthYear.format(d)); },
    dayMonth: function (d) { return F.dayMonth.format(d); },
    dayMonthShort: function (d) { return F.dayMonthShort.format(d).replace('.', ''); },
    dateLong: function (d) { return F.dateLong.format(d); },
    weekdaysShort: function () {
      var out = [];
      for (var i = 0; i < 7; i++) out.push(fmt.dayShort(new Date(2024, 0, 1 + i)));
      return out;
    },
    rel: function (d) {
      var diff = Math.round((App.dayStart(d) - App.dayStart(App.now())) / 864e5);
      if (diff >= -1 && diff <= 1 && F.rtf) return cap(F.rtf.format(diff, 'day'));
      return fmt.day(d);
    },
    range: function (a, b) {
      if (App.locale === 'en') {
        var same = (a.getHours() < 12) === (b.getHours() < 12);
        return (same ? fmt.time(a, false) : fmt.time(a)) + ' – ' + fmt.time(b);
      }
      return fmt.time(a) + ' – ' + fmt.time(b);
    }
  };

  App.initFormat();
})();
