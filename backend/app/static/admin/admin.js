(function () {
  'use strict';

  /* ------------------------------------------------------------------ i18n */
  var STR = {
    es: {
      nav_spotify: 'Spotify', sub_spotify: 'Controla desde el marco la música de tus altavoces con Spotify (Echo, Sonos, Chromecast, el móvil…). Hace falta una cuenta Premium.',
      nav_music: 'Música', scr_music: 'Música',
      sp_steps_h: 'Cómo conectarlo', sp_step1: 'En developer.spotify.com/dashboard crea una app (es gratis) y añade como «Redirect URI» exactamente la dirección de abajo.',
      sp_step2: 'Copia el Client ID de esa app aquí y guarda.', sp_step3: 'Pulsa «Conectar con Spotify» y acepta el permiso. Spotify te llevará a una página que no carga (es normal): copia la dirección completa de esa página y pégala aquí.',
      sp_enabled: 'Mostrar Música en los marcos', sp_client: 'Client ID', sp_redirect: 'Redirect URI', sp_connect: 'Guardar y conectar con Spotify', sp_open: 'Abrir Spotify para dar el permiso',
      sp_paste: 'Pega aquí la dirección a la que te ha llevado Spotify', sp_finish: 'Terminar conexión', sp_connected: 'Conectado', sp_notconnected: 'Sin conectar', sp_disconnect: 'Desconectar',
      sp_devices: 'Altavoces detectados', sp_no_devices: 'No hay ningún altavoz activo. Abre Spotify en uno para que aparezca.', sp_check: 'Comprobar altavoces',
      sp_limits: 'El propio marco no puede ser un altavoz de Spotify (su Android antiguo no lo permite): controla otros altavoces. Spotify solo deja controlar la reproducción a cuentas Premium.', sp_done: 'Spotify conectado.',
      al_frames_help: 'Si no marcas ninguno, suena en todos los marcos.', chores_none: 'Todavía no hay tareas. Añade la primera con los botones de abajo.',
      nav_alarms: 'Alarmas', sub_alarms: 'Alarmas que suenan en los marcos con un sonido, un mensaje o ambos. El mensaje puede leerse en voz alta.',
      al_add: 'Nueva alarma', al_time: 'Hora', al_name: 'Nombre', al_days: 'Qué días', al_date: 'O un día concreto (suena solo ese día)', al_sound: 'Sonido', al_message: 'Mensaje (se muestra en pantalla)',
      al_speak: 'Leer el mensaje en voz alta', al_volume: 'Volumen de la alarma', al_duration: 'Se para sola a los (segundos)', al_snooze: 'Minutos de posponer (0 = sin botón)',
      al_frames: 'En qué marcos suena', al_all_frames: 'En todos los marcos', al_test: 'Probar ahora', al_tested: 'Enviada a los marcos conectados.', al_none: 'Todavía no hay alarmas.',
      al_tts_help: 'La lectura en voz alta depende de que el marco tenga síntesis de voz (Android 6 puede no traerla). Usa «Probar ahora» para comprobarlo; si no habla, el mensaje se muestra igualmente.',
      al_off: 'Desactivada', al_sound_none: 'Sin sonido', al_once_on: 'El {d}', al_edit: 'Editar', al_close: 'Cerrar', al_untitled: 'Alarma sin nombre',
      snd_chime: 'Campanilla', snd_bell: 'Campana', snd_soft: 'Suave', snd_beep: 'Pitido', snd_melody: 'Melodía', snd_speak: 'Decir la hora en voz alta',
      night_color: 'Color del reloj nocturno', text_color: 'Color del texto en reposo', transition: 'Transición entre fotos', tr_fade: 'Fundido suave', tr_none: 'Corte directo',
      sleep_on_lights_off: 'Apagar la pantalla al detectar que se apaga la luz', lights_off_lux: 'Luz apagada por debajo de (lux)',
      lights_off_help: 'Si la luz de la habitación baja de golpe hasta casi la oscuridad, el marco entiende que han apagado la luz y apaga la pantalla.',
      sounds_h: 'Sonido', sounds_volume: 'Volumen del marco (%)', chime_enabled: 'Sonar a las horas en punto', chime_every: 'Cuándo', ev_hour: 'Cada hora en punto', ev_half: 'Cada media hora',
      chime_sound: 'Qué suena', chime_quiet: 'No molestar (silencio en este tramo)', quiet_start: 'Desde', quiet_end: 'Hasta', test_alert: 'Probar sonido y voz', test_msg: 'Prueba del marco',
      ch_kind_repeat: 'Se repite', ch_kind_once: 'Una sola vez', ch_new_once: 'Nueva tarea de una vez', ch_edit: 'Editar', ch_close: 'Cerrar', ch_untitled: 'Tarea sin título',
      ch_what: '¿Qué hay que hacer?', ch_who: '¿Quién la hace?', ch_who_help: 'Cada persona marcada tiene su propia casilla. Sin marcar a nadie es una tarea de toda la casa (una sola casilla).',
      ch_when: '¿Cuándo?', ch_every_day: 'Todos los días', ch_weekdays: 'Lunes a viernes', ch_weekend: 'Fin de semana', ch_due: 'Para el día',
      ch_once_help: 'Aparece en el marco a partir de ese día y se queda hasta que alguien la marca. Una vez hecha, desaparece al día siguiente. Si no se hace, se marca como pendiente.',
      ch_whole_house: 'Toda la casa', ch_paused: 'Pausada', ch_weeks_even: 'semanas pares', ch_weeks_odd: 'semanas impares', ch_weeks_every: 'cada {n} semanas',
      chores_help2: 'Las tareas aparecen en el marco (sección Tareas) y se marcan tocándolas. Las que se repiten se reinician cada día; las de una sola vez se quedan hasta que se hacen.',
      ch_quick: 'Atajos', days_full: 'lunes,martes,miércoles,jueves,viernes,sábado,domingo',
      ag_trigger: 'Solo disparadores (Home Assistant)', ag_ha_h: 'Home Assistant: abrir una cámara o dar un aviso en el marco',
      ag_ha_help: 'Crea una clave con permiso «Solo disparadores» y pégala en este fragmento. Solo puede enviar órdenes a los marcos: no lee ni cambia nada más.',
      ag_ha_use: 'Después, en una automatización: action: rest_command.homehq_camera (data: device: "Salón", camera: "puerta") o rest_command.homehq_aviso (data: message: "Llaman a la puerta").',
      nav_updates: 'Actualizaciones', sub_updates: 'Publica nuevas versiones de la app del marco para que se instalen por la red, sin cable USB.',
      upd_mode: 'Qué hacen los marcos con una versión nueva', upd_mode_off: 'Nada (actualizaciones desactivadas)', upd_mode_notify: 'Avisar y ofrecerla en Ajustes', upd_mode_auto: 'Descargarla sola y dejarla lista para instalar',
      upd_mode_help: 'Instalar siempre requiere un toque de confirmación en el marco: Android no permite que una app se instale sola sin permisos de sistema.',
      upd_upload_title: 'Subir una versión', upd_drop: 'Suelta aquí el APK o pulsa para elegirlo (kiosk/build/homehq.apk)', upd_notes: 'Novedades (opcional)',
      upd_releases: 'Versiones subidas', upd_none: 'Todavía no has subido ninguna versión.', upd_publish: 'Publicar', upd_unpublish: 'Retirar', upd_published: 'Publicada', upd_draft: 'Sin publicar',
      upd_mode_h: 'Comportamiento', upd_cert: 'Firma', upd_uploaded: 'Subido', upd_created: 'Versión subida. Publícala para que los marcos la vean.', upd_exists: 'Esa versión ya estaba subida.', upd_delete_confirm: '¿Borrar esta versión?',
      upd_publish_confirm: '¿Publicar esta versión? Los marcos la ofrecerán o la descargarán según el modo elegido.',
      upd_help: 'Flujo: 1) sube el número de versión en kiosk/build.sh, 2) ejecuta kiosk/build.sh, 3) sube kiosk/build/homehq.apk aquí, 4) publícalo. Un marco solo se actualiza a versiones con un versionCode mayor y firmadas con la misma clave.',
      command_update: 'Actualizar ahora', upd_outdated: 'Desactualizado', upd_ok: 'Al día', upd_cmd_sent: 'Orden enviada: el marco mostrará el diálogo de instalación', upd_version_col: 'App',
      nav_menu: 'Menú semanal', sub_menu: 'Desayuno, comida y cena de cada día. Puedes crear varias semanas que se repiten en orden.',
      meal_breakfast: 'Desayuno', meal_midmorning: 'Media mañana', meal_lunch: 'Comida', meal_snack: 'Merienda', meal_dinner: 'Cena',
      days_long: 'Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo',
      menu_current: 'Semana actual', menu_now_is: 'Esta semana es la {n}{name}', menu_next_is: 'La siguiente será la {n}{name}', menu_set_current: 'Esta semana es la…', menu_apply: 'Aplicar',
      menu_applied: 'Semana actual actualizada', menu_meals: 'Comidas que se muestran', menu_meals_help: 'Elige qué filas aparecen en el marco. Media mañana y merienda sirven para cosas iguales todos los días, como la fruta.',
      menu_weeks: 'Semanas del ciclo', menu_week: 'Semana {n}', menu_add_week: 'Añadir semana', menu_dup_week: 'Duplicar', menu_del_week: 'Eliminar semana',
      menu_del_confirm: '¿Eliminar esta semana del menú?', menu_move_left: 'Mover antes', menu_move_right: 'Mover después',
      menu_week_name: 'Nombre de la semana (opcional, p. ej. «Verano»)', menu_shared: 'Igual toda la semana',
      menu_shared_help: 'Lo que escribas aquí se muestra en una sola fila para toda la semana y sustituye a lo de cada día (útil para la fruta o el yogur).',
      menu_none: 'Todavía no hay menú. Crea la primera semana.', menu_first: 'Crear la primera semana',
      menu_rotation: 'Las semanas se repiten en orden: tras la última vuelve la primera. Cada lunes pasa a la siguiente.',
      nav_agents: 'Agentes (MCP)', sub_agents: 'Conecta un agente de IA para que configure y ajuste Home HQ por ti. Habla el protocolo MCP y usa tokens que puedes revocar cuando quieras.',
      ag_url: 'Dirección MCP', ag_new: 'Nuevo token', ag_name: 'Nombre (p. ej. «Cursor»)', ag_scope: 'Permisos', ag_read: 'Solo lectura', ag_full: 'Lectura y escritura',
      ag_exp: 'Caduca', ag_days: '{n} días', ag_create: 'Crear token', ag_once: 'Cópialo ahora: no se volverá a mostrar.', ag_config: 'Configuración para tu agente',
      ag_copy: 'Copiar', ag_copied: 'Copiado', ag_tokens: 'Tokens', ag_none: 'Aún no hay tokens.', ag_token: 'Token', ag_last: 'Último uso', ag_expires: 'Caduca',
      ag_revoke_confirm: '¿Revocar este token? Los agentes que lo usen dejarán de funcionar.', ag_revoked: 'Revocado', ag_expired: 'Caducado', ag_active: 'Activo',
      ag_security: 'Un token da acceso a la administración sin contraseña. Guárdalo como una contraseña, elige solo lectura si te basta y revócalo si se filtra. Los secretos (contraseñas de calendario, token de Home Assistant) nunca se pueden leer por esta vía, y un token no puede crear otros ni cambiar la contraseña.',
      ag_menu: 'Menú de navegación', ag_close: 'Cerrar menú',
      nav_screens: 'Pantallas', g_frames: 'Marcos', g_content: 'Contenido', g_integrations: 'Integraciones', g_system: 'Sistema',
      scr_home: 'Hoy', scr_calendar: 'Calendario', scr_photos: 'Fotos', scr_chores: 'Tareas', scr_house: 'Casa', scr_cameras: 'Cámaras', scr_shopping: 'Compra', scr_menu: 'Menú', scr_settings: 'Ajustes',
      screens_title: 'Orden de las pantallas', screens_help: 'Elige en qué orden aparecen las pantallas en la barra lateral del marco. «Hoy» siempre va la primera y «Ajustes» siempre la última, junto al reloj.',
      fixed_first: 'Siempre la primera', fixed_last: 'Siempre la última', move_up: 'Subir', move_down: 'Bajar', reset_order: 'Orden por defecto',
      sub_status: 'Estado de los servicios y de los marcos conectados.', sub_devices: 'Empareja marcos nuevos y ajusta pantalla, presencia y fotos de cada uno.',
      sub_photos: 'Álbumes que se muestran en los marcos.', sub_general: 'Idioma, zona horaria, ubicación y personas de la casa.',
      sub_calendars: 'Fuentes de calendario (ICS o CalDAV) que se muestran en los marcos.', sub_chores: 'Tareas del hogar que se marcan desde el marco.',
      sub_ha: 'Conexión con Home Assistant y entidades que se pueden usar desde los marcos.', sub_cameras: 'Cámaras de Frigate, Home Assistant o URL de imagen.',
      sub_shopping: 'De dónde sale la lista de la compra.', sub_sensor: 'Lectura en directo y grabaciones del sensor de luz para calibrar la presencia.',
      sub_account: 'Contraseña de administración.', sub_screens: 'Orden de las pantallas en la barra lateral de los marcos.',
      kpi_ha: 'Home Assistant', kpi_frames: 'Marcos emparejados', kpi_weather: 'Tiempo', kpi_server: 'Servidor', no_devices: 'Todavía no hay marcos emparejados.', saved_toast: 'Guardado',
      week_mode: 'Semanas en las que se repite', wm_all: 'Todas las semanas', wm_even: 'Semanas pares', wm_odd: 'Semanas impares', wm_every: 'Cada varias semanas',
      every_weeks: 'Cada cuántas semanas', start_week: 'Semana de inicio (cualquier día de esa semana)',
      week_help: 'Semanas pares/impares según el número de semana ISO (la semana del 19 de octubre de 2026 es la 43, impar). «Cada varias semanas» cuenta desde la semana de inicio.',
      nav_chores: 'Tareas', nav_cameras: 'Cámaras', chores: 'Tareas del hogar', add_chore: 'Añadir tarea', chore_title: 'Tarea', icon: 'Icono', time_opt: 'Hora (opcional)',
      chore_people: 'Quién la hace (sin marcar = tarea compartida de toda la casa)', chore_days: 'Días (sin marcar = todos los días)',
      days_short: 'L,M,X,J,V,S,D', chores_help: 'Cada persona marcada tiene su propia casilla cada día, así que «Hacer la cama» para dos hijos son dos casillas. Las tareas se marcan tocándolas en el marco (sección Tareas) y se reinician cada día.',
      people_help: 'Las personas sirven para dar color y dueño a los eventos de los calendarios y para repartir las tareas del hogar. No necesitan cuenta de Home Assistant: el enlace con una entidad person.* solo sirve para mostrar si están en casa.',
      frigate: 'Frigate', frigate_url: 'URL de Frigate', detect: 'Detectar cámaras de Frigate', detected: 'Cámaras detectadas: {n}', add_camera: 'Añadir cámara', source: 'Origen',
      src_frigate: 'Frigate', src_ha: 'Cámara de Home Assistant', src_url: 'URL de imagen (JPEG)', frigate_camera: 'Cámara de Frigate', ha_camera: 'Entidad camera.*', fps: 'Imágenes por segundo',
      preview: 'Vista previa', cameras_help: 'El servidor toma imágenes de la cámara y las reenvía a los marcos como vídeo; los marcos nunca se conectan directamente a Frigate ni a Home Assistant. Guarda antes de ver la vista previa.',
      customize: 'Personalizar', custom_name: 'Nombre en el marco', clear: 'Quitar', ha_custom_help: 'Las escenas, luces y persianas marcadas se pueden renombrar y cambiar de icono y color. Las cámaras se añaden en la sección Cámaras.',
      title: 'Administración', user: 'Usuario', password: 'Contraseña', login: 'Entrar', logout: 'Salir',
      bad_login: 'Usuario o contraseña incorrectos', too_many: 'Demasiados intentos. Espera unos minutos.',
      must_change: 'Debes cambiar la contraseña inicial antes de continuar.',
      current_pw: 'Contraseña actual', new_pw: 'Nueva contraseña (mínimo 10 caracteres)', change_pw: 'Cambiar contraseña',
      pw_changed: 'Contraseña cambiada', save: 'Guardar', saved: 'Guardado', cancel: 'Cancelar', delete: 'Eliminar', edit: 'Editar',
      nav_status: 'Resumen', nav_devices: 'Marcos', nav_photos: 'Fotos', nav_general: 'General', nav_calendars: 'Calendarios',
      nav_ha: 'Home Assistant', nav_shopping: 'Compra', nav_sensor: 'Sensor de luz', nav_account: 'Cuenta',
      pending_pairing: 'Solicitudes de emparejamiento', pairing_hint: 'Escribe el código de 6 dígitos que muestra el marco para aprobarlo.',
      code: 'Código', approve: 'Aprobar', reject: 'Rechazar', no_pending: 'No hay solicitudes pendientes.',
      devices: 'Marcos conectados', name: 'Nombre', status: 'Estado', online: 'conectado', offline: 'sin conexión',
      last_seen: 'Última conexión', never: 'nunca', revoke: 'Revocar', revoke_confirm: '¿Revocar este marco? Tendrá que emparejarse de nuevo.',
      command_wake: 'Despertar pantalla', command_sleep: 'Apagar pantalla', command_reload: 'Recargar', command_identify: 'Identificar',
      room: 'Estancia', language: 'Idioma', inherit: 'Heredar de general', timezone: 'Zona horaria', location: 'Ubicación (para el tiempo)',
      latitude: 'Latitud', longitude: 'Longitud', place_name: 'Nombre del lugar',
      display: 'Pantalla', presence: 'Presencia / actividad', photos_cfg: 'Fotos', layout: 'Pantalla principal',
      brightness_mode: 'Brillo', automatic: 'Automático', manual: 'Manual', always_on: 'Siempre encendida',
      brightness_min: 'Brillo mínimo (%)', brightness_max: 'Brillo máximo (%)', inactivity_timeout: 'Inactividad antes de apagar (s)',
      screen_off: 'Al apagar', never_off: 'No apagar', black: 'Pantalla negra', off: 'Apagar pantalla',
      night_mode: 'Modo nocturno', night_start: 'Inicio noche', night_end: 'Fin noche', night_brightness: 'Brillo nocturno (%)',
      enabled: 'Activado', provider: 'Fuente', light_sensor: 'Sensor de luz', homeassistant: 'Home Assistant', combined: 'Combinada', none: 'Ninguna',
      sensitivity: 'Sensibilidad', low: 'Baja', medium: 'Media', high: 'Alta', ha_entities: 'Sensores de presencia de HA',
      ha_hold: 'Mantener presencia HA (s)', min_abs_lux: 'Cambio mínimo absoluto (lux)', min_rel_change: 'Cambio relativo mínimo',
      min_gap: 'Separación mínima entre eventos (s)', hold: 'Duración de la actividad (s)',
      album: 'Álbum', no_album: '(sin álbum)', interval: 'Intervalo (s)', order: 'Orden', chronological: 'Cronológico', random: 'Aleatorio',
      fit: 'Ajuste', contain: 'Contener', cover: 'Cubrir', overlay: 'Leyenda sobre cada foto (cuándo y dónde se hizo)', widgets_h: 'Información sobre las fotos (marco en reposo)', widgets_help: 'Lo que se dibuja encima de las fotos cuando el marco está en reposo. Sin marcar, solo se ven las fotos.', wg_time: 'Hora', wg_date: 'Fecha', wg_weather: 'Tiempo', wg_calendar: 'Próximo evento', wg_tasks: 'Tareas pendientes', wg_people: 'Personas en casa', calendar_mode: 'Calendario: vista inicial', cal_mode_day: 'Día (por personas)', cal_mode_3day: 'Tres días', cal_mode_week: 'Semana', cal_mode_month: 'Mes', calendar_mode_help: 'Es la vista con la que se abre el calendario; en el marco se puede cambiar y vuelve a esta al pasar un rato.', cache_limit: 'Fotos en caché del marco',
      default_view: 'Vista inicial', ambient_after: 'Pasar a fotos tras (s)', home_after: 'Volver a inicio tras (s)',
      albums: 'Álbumes', new_album: 'Nuevo álbum', create: 'Crear', rename: 'Renombrar', upload: 'Subir fotos',
      drop_here: 'Arrastra fotos aquí o pulsa para elegirlas (JPEG, PNG, HEIC, WEBP)', uploading: 'Subiendo', of: 'de', duplicates: 'duplicadas',
      photos_n: 'fotos', delete_album_confirm: '¿Eliminar el álbum y todas sus fotos?', delete_photo_confirm: '¿Eliminar esta foto?', caption: 'Leyenda',
      people: 'Personas', add_person: 'Añadir persona', color: 'Color', ha_person: 'Entidad person.* de HA (opcional)',
      calendars: 'Calendarios', add_calendar: 'Añadir calendario', type: 'Tipo', url: 'URL', calendar_user: 'Usuario (CalDAV)',
      calendar_pw: 'Contraseña / token (se guarda cifrada)', calendar_name: 'Nombre del calendario (CalDAV, opcional)', refresh_min: 'Actualizar cada (min)',
      calendar_people: 'Personas de este calendario (vacío = eventos de toda la familia, sin columna de persona)', calendar_tag_help: 'Para asignar un evento concreto a alguien, escribe en sus notas @user:nombre (el nombre o el id de la persona; da igual mayúsculas y acentos). Con varias etiquetas se asigna a varias personas, y @user:familia lo deja como evento de todos. La etiqueta manda sobre las personas del calendario y no se muestra en el marco.', sync_now: 'Sincronizar ahora', synced: 'Sincronizado: {n} eventos',
      ha_url: 'URL de Home Assistant', ha_token: 'Token de acceso de larga duración', token_saved: 'Token guardado (no se puede volver a ver)',
      token_missing: 'Sin token', verify_tls: 'Verificar certificado TLS', test_conn: 'Probar conexión', conn_ok: 'Conexión correcta. HA {v}',
      ha_status: 'Estado de la conexión', connected: 'conectado', disconnected: 'desconectado',
      authorized: 'Entidades autorizadas (visibles y controlables desde los marcos)', filter: 'Filtrar', delete_token: 'Borrar token',
      shopping_provider: 'Fuente de la lista', local: 'Local (en este servidor)', ha_list: 'Home Assistant (lista todo.*, p. ej. Alexa)',
      ha_list_entity: 'Entidad de la lista', shopping_hint: 'Si no hay lista de HA configurada, se usa la lista local.',
      recording: 'Grabación de calibración', start_rec: 'Iniciar grabación', stop_rec: 'Detener', rec_name: 'Nombre de la grabación',
      recordings: 'Grabaciones', download: 'Descargar CSV', samples: 'muestras', live: 'Lectura en vivo', choose_device: 'Elige un marco',
      lux_now: 'Luz actual (lux)', server: 'Servidor', version: 'Versión', weather: 'Tiempo', configured: 'configurado', not_configured: 'sin configurar',
      sources: 'Fuentes de datos', details: 'Detalle', http_warn: 'Estás accediendo por HTTP. Usa un proxy inverso con HTTPS fuera de tu red local.',
      error: 'Error', loading: 'Cargando…', sure: '¿Seguro?', version_cfg: 'Versión de configuración', device_id: 'ID', ip: 'IP',
      app_version: 'App', hw: 'Hardware', close: 'Cerrar', pairing_expired: 'Caduca'
    },
    en: {
      nav_spotify: 'Spotify', sub_spotify: 'Control the music on your Spotify speakers (Echo, Sonos, Chromecast, a phone…) from the frame. Needs a Premium account.',
      nav_music: 'Music', scr_music: 'Music',
      sp_steps_h: 'How to connect it', sp_step1: 'At developer.spotify.com/dashboard create an app (it is free) and add exactly the address below as its “Redirect URI”.',
      sp_step2: 'Copy that app’s Client ID here and save.', sp_step3: 'Press “Connect with Spotify” and accept the permission. Spotify sends you to a page that does not load (that is normal): copy the full address of that page and paste it here.',
      sp_enabled: 'Show Music on the frames', sp_client: 'Client ID', sp_redirect: 'Redirect URI', sp_connect: 'Save and connect with Spotify', sp_open: 'Open Spotify to grant permission',
      sp_paste: 'Paste the address Spotify sent you to', sp_finish: 'Finish connecting', sp_connected: 'Connected', sp_notconnected: 'Not connected', sp_disconnect: 'Disconnect',
      sp_devices: 'Speakers found', sp_no_devices: 'No speaker is active. Open Spotify on one so it shows up.', sp_check: 'Check speakers',
      sp_limits: 'The frame itself cannot be a Spotify speaker (its old Android does not allow it): it controls other speakers. Spotify only lets Premium accounts control playback.', sp_done: 'Spotify connected.',
      al_frames_help: 'With none selected, it rings on every frame.', chores_none: 'There are no chores yet. Add the first one with the buttons below.',
      nav_alarms: 'Alarms', sub_alarms: 'Alarms that ring on the frames with a sound, a message or both. The message can be read aloud.',
      al_add: 'New alarm', al_time: 'Time', al_name: 'Name', al_days: 'Which days', al_date: 'Or one specific day (rings only that day)', al_sound: 'Sound', al_message: 'Message (shown on screen)',
      al_speak: 'Read the message aloud', al_volume: 'Alarm volume', al_duration: 'Stops by itself after (seconds)', al_snooze: 'Snooze minutes (0 = no button)',
      al_frames: 'Which frames ring', al_all_frames: 'All frames', al_test: 'Try it now', al_tested: 'Sent to the connected frames.', al_none: 'There are no alarms yet.',
      al_tts_help: 'Speech depends on the frame having a text-to-speech engine (Android 6 may not ship one). Use “Try it now” to check; if it stays silent, the message is still shown.',
      al_off: 'Off', al_sound_none: 'No sound', al_once_on: 'On {d}', al_edit: 'Edit', al_close: 'Close', al_untitled: 'Unnamed alarm',
      snd_chime: 'Chime', snd_bell: 'Bell', snd_soft: 'Soft', snd_beep: 'Beep', snd_melody: 'Melody', snd_speak: 'Say the time aloud',
      night_color: 'Night clock colour', text_color: 'Text colour on the idle screen', transition: 'Photo transition', tr_fade: 'Smooth fade', tr_none: 'Straight cut',
      sleep_on_lights_off: 'Turn the screen off when the room light goes out', lights_off_lux: 'Light counts as off below (lux)',
      lights_off_help: 'If the room light drops suddenly to near darkness, the frame assumes the light was switched off and turns the screen off.',
      sounds_h: 'Sound', sounds_volume: 'Frame volume (%)', chime_enabled: 'Chime on the hour', chime_every: 'When', ev_hour: 'Every hour', ev_half: 'Every half hour',
      chime_sound: 'What plays', chime_quiet: 'Do not disturb (silent in this window)', quiet_start: 'From', quiet_end: 'Until', test_alert: 'Test sound and voice', test_msg: 'Frame test',
      ch_kind_repeat: 'Repeats', ch_kind_once: 'One time only', ch_new_once: 'New one-off task', ch_edit: 'Edit', ch_close: 'Close', ch_untitled: 'Untitled chore',
      ch_what: 'What needs doing?', ch_who: 'Who does it?', ch_who_help: 'Every selected person gets their own checkbox. With nobody selected it is a household chore (one checkbox).',
      ch_when: 'When?', ch_every_day: 'Every day', ch_weekdays: 'Monday to Friday', ch_weekend: 'Weekend', ch_due: 'Due on',
      ch_once_help: 'It shows on the frame from that day and stays until somebody ticks it. Once done, it disappears the next day. If it is not done, it is flagged as overdue.',
      ch_whole_house: 'Whole household', ch_paused: 'Paused', ch_weeks_even: 'even weeks', ch_weeks_odd: 'odd weeks', ch_weeks_every: 'every {n} weeks',
      chores_help2: 'Chores show on the frame (Chores section) and are ticked by tapping them. Repeating ones reset every day; one-off ones stay until they are done.',
      ch_quick: 'Shortcuts', days_full: 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday',
      ag_trigger: 'Triggers only (Home Assistant)', ag_ha_h: 'Home Assistant: open a camera or show a notice on a frame',
      ag_ha_help: 'Create a key with the “Triggers only” scope and paste it into this snippet. It can only send commands to the frames: it cannot read or change anything else.',
      ag_ha_use: 'Then, in an automation: action: rest_command.homehq_camera (data: device: "Living room", camera: "door") or rest_command.homehq_aviso (data: message: "Someone is at the door").',
      nav_updates: 'Updates', sub_updates: 'Publish new versions of the frame app so they install over the network, no USB cable.',
      upd_mode: 'What frames do with a new version', upd_mode_off: 'Nothing (updates off)', upd_mode_notify: 'Notify and offer it in Settings', upd_mode_auto: 'Download it automatically and leave it ready to install',
      upd_mode_help: 'Installing always needs one confirmation tap on the frame: Android does not let an app install itself without system privileges.',
      upd_upload_title: 'Upload a version', upd_drop: 'Drop the APK here or click to choose it (kiosk/build/homehq.apk)', upd_notes: 'Release notes (optional)',
      upd_releases: 'Uploaded versions', upd_none: 'You have not uploaded any version yet.', upd_publish: 'Publish', upd_unpublish: 'Withdraw', upd_published: 'Published', upd_draft: 'Unpublished',
      upd_mode_h: 'Behaviour', upd_cert: 'Signature', upd_uploaded: 'Uploaded', upd_created: 'Version uploaded. Publish it so the frames can see it.', upd_exists: 'That version was already uploaded.', upd_delete_confirm: 'Delete this version?',
      upd_publish_confirm: 'Publish this version? Frames will offer or download it according to the selected mode.',
      upd_help: 'Flow: 1) raise the version number in kiosk/build.sh, 2) run kiosk/build.sh, 3) upload kiosk/build/homehq.apk here, 4) publish it. A frame only updates to a higher versionCode signed with the same key.',
      command_update: 'Update now', upd_outdated: 'Out of date', upd_ok: 'Up to date', upd_cmd_sent: 'Command sent: the frame will show the install dialog', upd_version_col: 'App',
      nav_menu: 'Weekly menu', sub_menu: 'Breakfast, lunch and dinner for each day. Create several weeks that repeat in order.',
      meal_breakfast: 'Breakfast', meal_midmorning: 'Mid-morning', meal_lunch: 'Lunch', meal_snack: 'Snack', meal_dinner: 'Dinner',
      days_long: 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday',
      menu_current: 'Current week', menu_now_is: 'This week is week {n}{name}', menu_next_is: 'Next week will be week {n}{name}', menu_set_current: 'This week is week…', menu_apply: 'Apply',
      menu_applied: 'Current week updated', menu_meals: 'Meals shown', menu_meals_help: 'Choose which rows appear on the frame. Mid-morning and snack suit things that are the same every day, like fruit.',
      menu_weeks: 'Weeks in the cycle', menu_week: 'Week {n}', menu_add_week: 'Add week', menu_dup_week: 'Duplicate', menu_del_week: 'Delete week',
      menu_del_confirm: 'Delete this week from the menu?', menu_move_left: 'Move earlier', menu_move_right: 'Move later',
      menu_week_name: 'Week name (optional, e.g. “Summer”)', menu_shared: 'Same all week',
      menu_shared_help: 'Whatever you write here is shown as a single row for the whole week and replaces each day’s entry (handy for fruit or yogurt).',
      menu_none: 'No menu yet. Create the first week.', menu_first: 'Create the first week',
      menu_rotation: 'Weeks repeat in order: after the last one the first returns. Each Monday moves to the next.',
      nav_agents: 'Agents (MCP)', sub_agents: 'Connect an AI agent so it can configure and tune Home HQ for you. It speaks the MCP protocol and uses tokens you can revoke at any time.',
      ag_url: 'MCP address', ag_new: 'New token', ag_name: 'Name (e.g. “Cursor”)', ag_scope: 'Permissions', ag_read: 'Read only', ag_full: 'Read and write',
      ag_exp: 'Expires', ag_days: '{n} days', ag_create: 'Create token', ag_once: 'Copy it now: it will not be shown again.', ag_config: 'Settings for your agent',
      ag_copy: 'Copy', ag_copied: 'Copied', ag_tokens: 'Tokens', ag_none: 'No tokens yet.', ag_token: 'Token', ag_last: 'Last used', ag_expires: 'Expires',
      ag_revoke_confirm: 'Revoke this token? Agents using it will stop working.', ag_revoked: 'Revoked', ag_expired: 'Expired', ag_active: 'Active',
      ag_security: 'A token gives access to the admin without a password. Keep it like a password, choose read-only when that is enough and revoke it if it leaks. Secrets (calendar passwords, the Home Assistant token) can never be read this way, and a token cannot create others or change the password.',
      ag_menu: 'Navigation menu', ag_close: 'Close menu',
      nav_screens: 'Screens', g_frames: 'Frames', g_content: 'Content', g_integrations: 'Integrations', g_system: 'System',
      scr_home: 'Today', scr_calendar: 'Calendar', scr_photos: 'Photos', scr_chores: 'Chores', scr_house: 'House', scr_cameras: 'Cameras', scr_shopping: 'Shopping', scr_menu: 'Menu', scr_settings: 'Settings',
      screens_title: 'Screen order', screens_help: 'Choose the order of the screens in the frame side bar. “Today” is always first and “Settings” is always last, next to the clock.',
      fixed_first: 'Always first', fixed_last: 'Always last', move_up: 'Move up', move_down: 'Move down', reset_order: 'Default order',
      sub_status: 'Health of the services and of the connected frames.', sub_devices: 'Pair new frames and tune display, presence and photos for each one.',
      sub_photos: 'Albums shown on the frames.', sub_general: 'Language, time zone, location and household members.',
      sub_calendars: 'Calendar sources (ICS or CalDAV) shown on the frames.', sub_chores: 'Household chores that are ticked from the frame.',
      sub_ha: 'Home Assistant connection and entities the frames may use.', sub_cameras: 'Frigate, Home Assistant or image URL cameras.',
      sub_shopping: 'Where the shopping list comes from.', sub_sensor: 'Live reading and recordings of the light sensor to calibrate presence.',
      sub_account: 'Administration password.', sub_screens: 'Order of the screens in the frame side bar.',
      kpi_ha: 'Home Assistant', kpi_frames: 'Paired frames', kpi_weather: 'Weather', kpi_server: 'Server', no_devices: 'No frames are paired yet.', saved_toast: 'Saved',
      week_mode: 'Weeks it repeats', wm_all: 'Every week', wm_even: 'Even weeks', wm_odd: 'Odd weeks', wm_every: 'Every few weeks',
      every_weeks: 'Every how many weeks', start_week: 'Starting week (any day of that week)',
      week_help: 'Even/odd weeks follow the ISO week number (the week of 19 October 2026 is week 43, odd). “Every few weeks” counts from the starting week.',
      nav_chores: 'Chores', nav_cameras: 'Cameras', chores: 'Household chores', add_chore: 'Add chore', chore_title: 'Chore', icon: 'Icon', time_opt: 'Time (optional)',
      chore_people: 'Who does it (none selected = one shared chore for the whole house)', chore_days: 'Days (none selected = every day)',
      days_short: 'M,T,W,T,F,S,S', chores_help: 'Every selected person gets their own checkbox each day, so “Make the bed” for two children is two checkboxes. Chores are ticked by tapping them on the frame (Chores section) and reset every day.',
      people_help: 'People give calendar events a colour and an owner and let you assign household chores. They do not need a Home Assistant account: linking a person.* entity only shows whether they are at home.',
      frigate: 'Frigate', frigate_url: 'Frigate URL', detect: 'Detect Frigate cameras', detected: 'Cameras found: {n}', add_camera: 'Add camera', source: 'Source',
      src_frigate: 'Frigate', src_ha: 'Home Assistant camera', src_url: 'Image URL (JPEG)', frigate_camera: 'Frigate camera', ha_camera: 'camera.* entity', fps: 'Frames per second',
      preview: 'Preview', cameras_help: 'The server grabs images from the camera and relays them to the frames as video; frames never connect to Frigate or Home Assistant directly. Save before using the preview.',
      customize: 'Customise', custom_name: 'Name on the frame', clear: 'Clear', ha_custom_help: 'Selected scenes, lights and blinds can be renamed and given another icon and colour. Cameras are added in the Cameras section.',
      title: 'Administration', user: 'User', password: 'Password', login: 'Sign in', logout: 'Sign out',
      bad_login: 'Wrong username or password', too_many: 'Too many attempts. Wait a few minutes.',
      must_change: 'You must change the initial password before continuing.',
      current_pw: 'Current password', new_pw: 'New password (at least 10 characters)', change_pw: 'Change password',
      pw_changed: 'Password changed', save: 'Save', saved: 'Saved', cancel: 'Cancel', delete: 'Delete', edit: 'Edit',
      nav_status: 'Overview', nav_devices: 'Frames', nav_photos: 'Photos', nav_general: 'General', nav_calendars: 'Calendars',
      nav_ha: 'Home Assistant', nav_shopping: 'Shopping', nav_sensor: 'Light sensor', nav_account: 'Account',
      pending_pairing: 'Pairing requests', pairing_hint: 'Type the 6-digit code shown on the frame to approve it.',
      code: 'Code', approve: 'Approve', reject: 'Reject', no_pending: 'No pending requests.',
      devices: 'Connected frames', name: 'Name', status: 'Status', online: 'online', offline: 'offline',
      last_seen: 'Last seen', never: 'never', revoke: 'Revoke', revoke_confirm: 'Revoke this frame? It will have to pair again.',
      command_wake: 'Wake screen', command_sleep: 'Turn screen off', command_reload: 'Reload', command_identify: 'Identify',
      room: 'Room', language: 'Language', inherit: 'Inherit from general', timezone: 'Time zone', location: 'Location (for weather)',
      latitude: 'Latitude', longitude: 'Longitude', place_name: 'Place name',
      display: 'Display', presence: 'Presence / activity', photos_cfg: 'Photos', layout: 'Main screen',
      brightness_mode: 'Brightness', automatic: 'Automatic', manual: 'Manual', always_on: 'Always on',
      brightness_min: 'Minimum brightness (%)', brightness_max: 'Maximum brightness (%)', inactivity_timeout: 'Inactivity before screen off (s)',
      screen_off: 'When off', never_off: 'Never turn off', black: 'Black screen', off: 'Screen off',
      night_mode: 'Night mode', night_start: 'Night starts', night_end: 'Night ends', night_brightness: 'Night brightness (%)',
      enabled: 'Enabled', provider: 'Source', light_sensor: 'Light sensor', homeassistant: 'Home Assistant', combined: 'Combined', none: 'None',
      sensitivity: 'Sensitivity', low: 'Low', medium: 'Medium', high: 'High', ha_entities: 'HA presence sensors',
      ha_hold: 'Hold HA presence (s)', min_abs_lux: 'Minimum absolute change (lux)', min_rel_change: 'Minimum relative change',
      min_gap: 'Minimum gap between events (s)', hold: 'Activity duration (s)',
      album: 'Album', no_album: '(no album)', interval: 'Interval (s)', order: 'Order', chronological: 'Chronological', random: 'Random',
      fit: 'Fit', contain: 'Contain', cover: 'Cover', overlay: 'Caption on each photo (when and where it was taken)', widgets_h: 'Information over the photos (idle frame)', widgets_help: 'What is drawn over the photos while the frame is idle. With none ticked, only the photos show.', wg_time: 'Time', wg_date: 'Date', wg_weather: 'Weather', wg_calendar: 'Next event', wg_tasks: 'Pending chores', wg_people: 'People at home', calendar_mode: 'Calendar: opening view', cal_mode_day: 'Day (by person)', cal_mode_3day: 'Three days', cal_mode_week: 'Week', cal_mode_month: 'Month', calendar_mode_help: 'The view the calendar opens with; it can be changed on the frame and returns to this one after a while.', cache_limit: 'Photos cached on the frame',
      default_view: 'Start view', ambient_after: 'Go to photos after (s)', home_after: 'Back to home after (s)',
      albums: 'Albums', new_album: 'New album', create: 'Create', rename: 'Rename', upload: 'Upload photos',
      drop_here: 'Drop photos here or click to choose (JPEG, PNG, HEIC, WEBP)', uploading: 'Uploading', of: 'of', duplicates: 'duplicates',
      photos_n: 'photos', delete_album_confirm: 'Delete the album and all its photos?', delete_photo_confirm: 'Delete this photo?', caption: 'Caption',
      people: 'People', add_person: 'Add person', color: 'Color', ha_person: 'HA person.* entity (optional)',
      calendars: 'Calendars', add_calendar: 'Add calendar', type: 'Type', url: 'URL', calendar_user: 'User (CalDAV)',
      calendar_pw: 'Password / token (stored encrypted)', calendar_name: 'Calendar name (CalDAV, optional)', refresh_min: 'Refresh every (min)',
      calendar_people: 'People of this calendar (empty = whole-family events, no person column)', calendar_tag_help: 'To give one event to someone, write @user:name in its notes (the person\'s name or id; case and accents do not matter). Several tags assign several people, and @user:family makes it everyone\'s. The tag wins over the calendar\'s people and is not shown on the frame.', sync_now: 'Sync now', synced: 'Synced: {n} events',
      ha_url: 'Home Assistant URL', ha_token: 'Long-lived access token', token_saved: 'Token stored (cannot be shown again)',
      token_missing: 'No token', verify_tls: 'Verify TLS certificate', test_conn: 'Test connection', conn_ok: 'Connection OK. HA {v}',
      ha_status: 'Connection status', connected: 'connected', disconnected: 'disconnected',
      authorized: 'Authorised entities (visible and controllable from the frames)', filter: 'Filter', delete_token: 'Delete token',
      shopping_provider: 'List source', local: 'Local (on this server)', ha_list: 'Home Assistant (todo.* list, e.g. Alexa)',
      ha_list_entity: 'List entity', shopping_hint: 'Without a configured HA list the local list is used.',
      recording: 'Calibration recording', start_rec: 'Start recording', stop_rec: 'Stop', rec_name: 'Recording name',
      recordings: 'Recordings', download: 'Download CSV', samples: 'samples', live: 'Live reading', choose_device: 'Choose a frame',
      lux_now: 'Current light (lux)', server: 'Server', version: 'Version', weather: 'Weather', configured: 'configured', not_configured: 'not configured',
      sources: 'Data sources', details: 'Details', http_warn: 'You are using plain HTTP. Put a reverse proxy with HTTPS in front of this outside your LAN.',
      error: 'Error', loading: 'Loading…', sure: 'Are you sure?', version_cfg: 'Config version', device_id: 'ID', ip: 'IP',
      app_version: 'App', hw: 'Hardware', close: 'Close', pairing_expired: 'Expires'
    }
  };
  var lang = localStorage.getItem('hq_admin_lang') || ((navigator.language || 'es').slice(0, 2) === 'en' ? 'en' : 'es');
  function t(k, vars) {
    var s = (STR[lang] && STR[lang][k]) || STR.es[k] || k;
    if (vars) Object.keys(vars).forEach(function (v) { s = s.replace('{' + v + '}', vars[v]); });
    return s;
  }

  /* ------------------------------------------------------------------ DOM helpers (text only, never innerHTML) */
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === 'class') el.className = v;
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
      else if (k === 'value') el.value = v;
      else if (k === 'checked') el.checked = !!v;
      else el.setAttribute(k, v === true ? '' : v);
    });
    for (var i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }
  function add(el, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(el, x); });
    else el.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  /* ------------------------------------------------------------------ API with transparent refresh */
  var refreshing = null;
  function rawFetch(method, path, body, opts) {
    var init = { method: method, credentials: 'same-origin', headers: { 'X-HomeHQ-Admin': '1' } };
    if (body !== undefined) {
      if (opts && opts.raw) { init.body = body; init.headers['Content-Type'] = 'application/octet-stream'; }
      else { init.body = JSON.stringify(body); init.headers['Content-Type'] = 'application/json'; }
    }
    return fetch(path, init);
  }
  function api(method, path, body, opts) {
    return rawFetch(method, path, body, opts).then(function (r) {
      if (r.status === 401 && path.indexOf('/auth/') < 0) {
        refreshing = refreshing || rawFetch('POST', '/api/v1/admin/auth/refresh').then(function (x) { return x.ok; })
          .finally(function () { setTimeout(function () { refreshing = null; }, 0); });
        return refreshing.then(function (ok) {
          if (!ok) { showLogin(); throw new Error('session'); }
          return rawFetch(method, path, body, opts).then(parse);
        });
      }
      return parse(r);
    });
  }
  function parse(r) {
    return r.text().then(function (txt) {
      var data = null;
      try { data = txt ? JSON.parse(txt) : null; } catch (e) { data = null; }
      if (!r.ok) {
        var d = data && data.detail;
        if (Array.isArray(d)) d = d.map(function (x) { return (x.loc || []).slice(1).join('.') + ': ' + x.msg; }).join('; ');
        var err = new Error(d || ('HTTP ' + r.status));
        err.status = r.status;
        throw err;
      }
      return data;
    });
  }

  /* ------------------------------------------------------------------ app shell */
  var root = document.getElementById('app');
  var state = { user: null, view: 'status', timers: [] };
  var main = null;

  function stopTimers() { state.timers.forEach(clearInterval); state.timers = []; }
  function banner(kind, text) { return h('div', { class: 'msg ' + kind, role: kind === 'err' ? 'alert' : 'status' }, text); }
  function flash(container, kind, text) {
    var stack = document.getElementById('toasts');
    if (!stack) { stack = h('div', { class: 'toasts', id: 'toasts', 'aria-live': 'polite' }); document.body.appendChild(stack); }
    var el = h('div', { class: 'toast ' + kind, role: kind === 'err' ? 'alert' : 'status' }, icon(kind === 'err' ? 'alert' : 'ok'), h('span', null, text));
    stack.appendChild(el);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, kind === 'err' ? 9000 : 3200);
  }
  function fail(e) { if (e.message !== 'session') flash(main || root, 'err', e.message); }

  function showLogin(message) {
    stopTimers();
    clear(root);
    var user = h('input', { id: 'u', autocomplete: 'username', value: 'admin' });
    var pw = h('input', { id: 'p', type: 'password', autocomplete: 'current-password' });
    var box = h('div', { class: 'login' });
    function submit(ev) {
      ev.preventDefault();
      rawFetch('POST', '/api/v1/admin/auth/login', { username: user.value, password: pw.value }).then(function (r) {
        if (r.status === 429) throw new Error(t('too_many'));
        if (!r.ok) throw new Error(t('bad_login'));
        return r.json();
      }).then(function (u) { state.user = u; boot(); })
        .catch(function (e) { flash(box, 'err', e.message); });
    }
    root.appendChild(box);
    add(box, [
      h('div', { class: 'logo' }, icon('photos')), h('h1', null, 'Home HQ'), h('p', { class: 'muted' }, t('title')),
      message ? banner('err', message) : null,
      h('form', { onsubmit: submit, class: 'card' },
        h('label', { for: 'u' }, t('user')), user,
        h('label', { for: 'p', style: null }, t('password')), pw,
        h('button', { class: 'btn pri', type: 'submit' }, t('login')))
    ]);
    pw.focus();
  }

  function showForcedPasswordChange() {
    clear(root);
    var box = h('div', { class: 'login' });
    root.appendChild(box);
    box.appendChild(h('h1', null, 'Home HQ'));
    box.appendChild(banner('err', t('must_change')));
    box.appendChild(passwordForm(function () { state.user.must_change_password = false; boot(); }));
  }

  function passwordForm(onDone) {
    var cur = h('input', { type: 'password', autocomplete: 'current-password' });
    var neu = h('input', { type: 'password', autocomplete: 'new-password', minlength: 10 });
    var form = h('form', { class: 'card', onsubmit: function (ev) {
      ev.preventDefault();
      api('POST', '/api/v1/admin/auth/password', { current_password: cur.value, new_password: neu.value })
        .then(function () { flash(form, 'ok', t('pw_changed')); cur.value = ''; neu.value = ''; if (onDone) onDone(); })
        .catch(function (e) { flash(form, 'err', e.message); });
    } }, h('label', null, t('current_pw')), cur, h('label', null, t('new_pw')), neu, h('p'),
      h('button', { class: 'btn pri', type: 'submit' }, t('change_pw')));
    return form;
  }

  var ICONS = {
    status: ['M22 12h-4l-3 9L9 3l-3 9H2'],
    updates: ['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4', 'M7 10l5 5 5-5', 'M12 15V3'],
    devices: ['M4 5h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z', 'M8 21h8', 'M12 18v3'],
    screens: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3 6h.01', 'M3 12h.01', 'M3 18h.01'],
    photos: ['M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z', 'M22 16l-5-5-9 9'],
    calendars: ['M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M16 2v4', 'M8 2v4', 'M3 10h18'],
    chores: ['M9 11l3 3L22 4', 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'],
    shopping: ['M9 22a1 1 0 1 0 0-2 1 1 0 0 0 0 2z', 'M20 22a1 1 0 1 0 0-2 1 1 0 0 0 0 2z', 'M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6'],
    cameras: ['M23 7l-7 5 7 5V7z', 'M3 5h11a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z'],
    ha: ['M3 11l9-8 9 8', 'M5 10v10h14V10', 'M10 20v-6h4v6'],
    sensor: ['M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z', 'M12 1v2', 'M12 21v2', 'M4.2 4.2l1.4 1.4', 'M18.4 18.4l1.4 1.4', 'M1 12h2', 'M21 12h2', 'M4.2 19.8l1.4-1.4', 'M18.4 5.6l1.4-1.4'],
    general: ['M4 21v-7', 'M4 10V3', 'M12 21v-9', 'M12 8V3', 'M20 21v-5', 'M20 12V3', 'M1 14h6', 'M9 8h6', 'M17 16h6'],
    account: ['M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
    logout: ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'M16 17l5-5-5-5', 'M21 12H9'],
    lang: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z', 'M2 12h20', 'M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20'],
    spotify: ['M9 18V5l12-2v13', 'M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0z', 'M21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z'],
    alarms: ['M12 22a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 8v5l3 2', 'M5 3L2 6', 'M22 6l-3-3'],
    up: ['M18 15l-6-6-6 6'], down: ['M6 9l6 6 6-6'],
    ok: ['M20 6L9 17l-5-5'], alert: ['M12 8v5', 'M12 16h.01', 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z'],
    menu: ['M7 3v8', 'M4.5 3v5a2.5 2.5 0 0 0 5 0V3', 'M7 11v10', 'M17 21V3c-2.5 1.5-3.5 4-3.5 8h3.5'],
    agents: ['M12 2v4', 'M7 6h10a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3z', 'M9 12h.01', 'M15 12h.01', 'M9 21h6'],
    burger: ['M4 6h16', 'M4 12h16', 'M4 18h16'], close: ['M18 6L6 18', 'M6 6l12 12'], plus: ['M12 5v14', 'M5 12h14'], copy: ['M9 9h11v11H9z', 'M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1'],
    lock: ['M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z', 'M7 11V7a5 5 0 0 1 10 0v4']
  };
  function icon(name) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('class', 'ic');
    svg.setAttribute('aria-hidden', 'true');
    (ICONS[name] || []).forEach(function (d) {
      var p = document.createElementNS(ns, 'path');
      p.setAttribute('d', d);
      svg.appendChild(p);
    });
    return svg;
  }

  var NAV = [
    ['g_frames', [['status', 'nav_status'], ['devices', 'nav_devices'], ['screens', 'nav_screens'], ['updates', 'nav_updates']]],
    ['g_content', [['photos', 'nav_photos'], ['calendars', 'nav_calendars'], ['chores', 'nav_chores'], ['alarms', 'nav_alarms'], ['shopping', 'nav_shopping'], ['cameras', 'nav_cameras'], ['menu', 'nav_menu']]],
    ['g_integrations', [['ha', 'nav_ha'], ['spotify', 'nav_spotify'], ['sensor', 'nav_sensor'], ['agents', 'nav_agents']]],
    ['g_system', [['general', 'nav_general'], ['account', 'nav_account']]]
  ];

  function boot() {
    if (state.user && state.user.must_change_password) return showForcedPasswordChange();
    renderShell();
    go(state.view);
  }

  function renderShell() {
    clear(root);
    var side = h('nav', { class: 'side' }, h('div', { class: 'brand' }, h('i', null, icon('photos')), 'Home HQ'));
    NAV.forEach(function (g) {
      side.appendChild(h('div', { class: 'group' }, t(g[0])));
      g[1].forEach(function (n) {
        side.appendChild(h('button', { 'data-v': n[0], class: n[0] === state.view ? 'on' : '', onclick: function () { go(n[0]); } }, icon(n[0]), t(n[1])));
      });
    });
    side.appendChild(h('div', { class: 'grow' }));
    side.appendChild(h('button', { class: 'quiet', onclick: function () { lang = lang === 'es' ? 'en' : 'es'; localStorage.setItem('hq_admin_lang', lang); document.documentElement.lang = lang; renderShell(); go(state.view); } }, icon('lang'), lang === 'es' ? 'English' : 'Español'));
    side.appendChild(h('button', { class: 'quiet', onclick: logout }, icon('logout'), t('logout') + ' (' + state.user.username + ')'));
    main = h('main');
    var bar = h('header', { class: 'topbar' },
      h('button', { class: 'tb', type: 'button', 'aria-label': t('ag_menu'), 'aria-controls': 'sidenav', 'aria-expanded': 'false', onclick: function () { toggleNav(); } }, icon('burger')),
      h('div', { class: 'tb-title', id: 'tbTitle' }, 'Home HQ'));
    side.id = 'sidenav';
    root.appendChild(h('div', { class: 'shell' }, bar, side, h('div', { class: 'scrim', onclick: function () { toggleNav(false); } }), main));
    watchTables();
  }

  /* Off-canvas navigation on small screens. */
  function toggleNav(open) {
    var on = open == null ? !document.body.classList.contains('nav-open') : open;
    document.body.classList.toggle('nav-open', on);
    var b = document.querySelector('.topbar .tb');
    if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false');
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') toggleNav(false); });

  /* Tables become stacked cards on phones: every cell remembers the header it sits under. */
  var tableWatch = null;
  function labelTables() {
    Array.prototype.forEach.call(document.querySelectorAll('main table'), function (tb) {
      var rows = tb.querySelectorAll('tr');
      if (!rows.length || tb.getAttribute('data-l') === String(rows.length)) return;
      var heads = Array.prototype.map.call(rows[0].children, function (c) { return c.textContent; });
      rows[0].className = 'thead';
      Array.prototype.forEach.call(rows, function (r, i) {
        if (i === 0) return;
        Array.prototype.forEach.call(r.children, function (c, n) { c.setAttribute('data-label', heads[n] || ''); });
      });
      tb.setAttribute('data-l', String(rows.length));
    });
  }
  function watchTables() {
    if (tableWatch) tableWatch.disconnect();
    if (!window.MutationObserver || !main) return;
    tableWatch = new MutationObserver(labelTables);
    tableWatch.observe(main, { childList: true, subtree: true });
  }

  function logout() {
    api('POST', '/api/v1/admin/auth/logout').catch(function () {}).then(function () { state.user = null; showLogin(); });
  }

  function go(view) {
    stopTimers();
    toggleNav(false);
    state.view = view;
    Array.prototype.forEach.call(document.querySelectorAll('nav.side button[data-v]'), function (b) {
      b.className = b.getAttribute('data-v') === view ? 'on' : '';
    });
    clear(main);
    main.appendChild(h('p', { class: 'muted' }, t('loading')));
    (VIEWS[view] || VIEWS.status)().catch(fail);
  }

  function page(title, nodes) {
    clear(main);
    var sub = t('sub_' + state.view);
    var tb = document.getElementById('tbTitle');
    if (tb) tb.textContent = title;
    main.appendChild(h('div', { class: 'page-head' }, h('h2', null, title), sub !== 'sub_' + state.view ? h('p', null, sub) : null));
    add(main, nodes);
    window.scrollTo(0, 0);
  }

  /* ------------------------------------------------------------------ form helpers */
  function get(o, path) { return path.split('.').reduce(function (a, k) { return a == null ? a : a[k]; }, o); }
  function set(o, path, v) {
    var ks = path.split('.'), last = ks.pop();
    var tgt = ks.reduce(function (a, k) { return a[k]; }, o);
    tgt[last] = v;
  }
  function input(obj, path, label, o) {
    o = o || {};
    var type = o.type || 'text';
    var el = h('input', { type: type, value: get(obj, path) == null ? '' : get(obj, path), min: o.min, max: o.max, step: o.step, placeholder: o.placeholder, autocomplete: 'off' });
    el.addEventListener('input', function () {
      var v = el.value;
      if (type === 'number') v = v === '' ? null : Number(v);
      set(obj, path, o.nullable && v === '' ? null : v);
    });
    return h('div', null, h('label', null, label), el);
  }
  function check(obj, path, label) {
    var el = h('input', { type: 'checkbox', checked: !!get(obj, path) });
    el.addEventListener('change', function () { set(obj, path, el.checked); });
    return h('label', { class: 'chk' }, el, label);
  }
  function select(obj, path, label, options, o) {
    o = o || {};
    var el = h('select');
    options.forEach(function (op) {
      var cur = get(obj, path);
      el.appendChild(h('option', { value: op[0], selected: (cur == null ? '' : cur) === op[0] }, op[1]));
    });
    el.addEventListener('change', function () { set(obj, path, o.nullable && el.value === '' ? null : el.value); });
    return h('div', null, h('label', null, label), el);
  }
  function color(obj, path, label) {
    var el = h('input', { type: 'color', value: get(obj, path) || '#ffffff' });
    el.addEventListener('input', function () { set(obj, path, el.value.toUpperCase()); });
    return h('div', null, h('label', null, label), el);
  }
  function seg(options, current, pick) {
    return h('div', { class: 'seg', role: 'group' }, options.map(function (o) {
      return h('button', { type: 'button', class: 'seg-b' + (o[0] === current ? ' on' : ''), 'aria-pressed': o[0] === current ? 'true' : 'false', onclick: function () { pick(o[0]); } }, o[1]);
    }));
  }
  function daysText(days) {
    var d = (days || []).slice().sort(), names = t('days_full').split(',');
    if (!d.length || d.length === 7) return t('ch_every_day');
    if (d.join() === '0,1,2,3,4') return t('ch_weekdays');
    if (d.join() === '5,6') return t('ch_weekend');
    return d.map(function (n) { return names[n]; }).join(', ');
  }
  function dayLabel(iso) {
    if (!iso) return '—';
    return new Date(iso + 'T12:00:00').toLocaleDateString(lang === 'en' ? 'en-GB' : 'es-ES', { weekday: 'short', day: 'numeric', month: 'short' });
  }
  function dayChips(arr) {
    var row = h('div', { class: 'row tight' });
    t('days_short').split(',').forEach(function (d, n) {
      var el = h('input', { type: 'checkbox', checked: arr.indexOf(n) >= 0 });
      el.addEventListener('change', function () { var k = arr.indexOf(n); if (k >= 0) arr.splice(k, 1); if (el.checked) arr.push(n); arr.sort(); });
      row.appendChild(h('label', { class: 'chk' }, el, d));
    });
    return row;
  }
  function btn(label, fn, cls) {
    var b = h('button', { class: 'btn ' + (cls || ''), type: 'button' }, label);
    b.addEventListener('click', function () {
      b.disabled = true;
      Promise.resolve().then(fn).catch(fail).finally(function () { b.disabled = false; });
    });
    return b;
  }
  function fmtDate(iso) {
    if (!iso) return t('never');
    var d = new Date(iso.endsWith('Z') || iso.indexOf('+') > 10 ? iso : iso + 'Z');
    return d.toLocaleString(lang === 'es' ? 'es-ES' : 'en-GB');
  }

  /* ------------------------------------------------------------------ views */
  var VIEWS = {};

  VIEWS.status = function () {
    return api('GET', '/api/v1/admin/status').then(function (s) {
      function tile(label, value, tone, detail) {
        return h('div', { class: 'stat' }, h('small', null, label), h('b', null, tone ? h('i', { class: 'dot ' + tone }) : null, value), detail ? h('span', null, detail) : null);
      }
      var ha = s.homeassistant;
      var rows = h('div', { class: 'stats' },
        tile(t('kpi_ha'), !ha.enabled ? t('not_configured') : (ha.connected ? t('connected') : t('disconnected')), !ha.enabled ? '' : (ha.connected ? 'ok' : 'bad'),
          ha.connected ? 'HA ' + ha.version + ' · ' + ha.entities + ' entities' : (ha.error || '')),
        tile(t('kpi_weather'), s.weather.configured ? (s.weather.ok ? 'OK' : t('error')) : t('not_configured'), s.weather.configured ? (s.weather.ok ? 'ok' : 'bad') : ''),
        tile(t('kpi_frames'), String(s.devices), s.devices ? 'ok' : 'warn', s.devices ? '' : t('no_devices')),
        tile(t('kpi_server'), 'v' + s.version, 'ok'));
      var nodes = [];
      if (location.protocol === 'http:' && ['localhost', '127.0.0.1'].indexOf(location.hostname) < 0 && !/^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(location.hostname)) nodes.push(banner('err', t('http_warn')));
      nodes.push(rows);
      var cal = h('table', null, h('tr', null, h('th', null, t('nav_calendars')), h('th', null, t('status')), h('th', null, t('details'))));
      s.calendars.forEach(function (c) {
        cal.appendChild(h('tr', null, h('td', null, c.name), h('td', null, h('span', { class: 'pill ' + (c.ok ? 'ok' : (c.ok === false ? 'bad' : '')) }, c.ok ? 'OK' : (c.ok === false ? t('error') : '—'))), h('td', { class: 'muted' }, c.detail || fmtDate(c.last_success))));
      });
      if (s.calendars.length) nodes.push(h('div', { class: 'card' }, h('h3', null, t('sources')), cal));
      page(t('nav_status'), nodes);
    });
  };

  /* ---- devices */
  VIEWS.devices = function () {
    return Promise.all([api('GET', '/api/v1/admin/pairing'), api('GET', '/api/v1/admin/devices'), api('GET', '/api/v1/admin/albums'), api('GET', '/api/v1/admin/config'), api('GET', '/api/v1/admin/updates')])
      .then(function (r) {
        var pairing = r[0], devices = r[1], albums = r[2], cfg = r[3].config, updates = r[4];
        var nodes = [];
        var pc = h('div', { class: 'card' }, h('h3', null, t('pending_pairing')), h('p', { class: 'muted' }, t('pairing_hint')));
        if (!pairing.length) pc.appendChild(h('p', null, t('no_pending')));
        pairing.forEach(function (p) {
          var code = h('input', { inputmode: 'numeric', maxlength: 6, placeholder: '000000', autocomplete: 'off' });
          var hintName = (p.hint && (p.hint.name || p.hint.model)) || '';
          var name = h('input', { placeholder: t('name'), value: hintName });
          pc.appendChild(h('div', { class: 'row', style: null },
            h('div', null, h('label', null, t('code')), code),
            h('div', null, h('label', null, t('name')), name),
            h('div', { class: 'muted' }, (p.ip || '') + ' · ' + t('pairing_expired') + ' ' + fmtDate(p.expires_at)),
            h('div', { class: 'row tight' }, btn(t('approve'), function () {
              return api('POST', '/api/v1/admin/pairing/' + p.id + '/approve', { code: code.value.trim(), name: name.value.trim() || hintName || 'Marco' }).then(function () { go('devices'); });
            }, 'pri'), btn(t('reject'), function () { return api('POST', '/api/v1/admin/pairing/' + p.id + '/reject').then(function () { go('devices'); }); }))));
        });
        nodes.push(pc);
        var dc = h('div', { class: 'card' }, h('h3', null, t('devices')));
        var tb = h('table', null, h('tr', null, h('th', null, t('name')), h('th', null, t('status')), h('th', null, t('last_seen')), h('th', null, t('upd_version_col')), h('th', null, '')));
        devices.forEach(function (d) {
          tb.appendChild(h('tr', null, h('td', null, d.name), h('td', null, h('span', { class: 'pill ' + (d.online ? 'ok' : '') }, d.online ? t('online') : t('offline'))),
            h('td', { class: 'muted' }, fmtDate(d.last_seen_at)), h('td', null, appVersionCell(d.app_version, updates.published)), h('td', null, btn(t('edit'), function () { return deviceEditor(d.id, albums, cfg); }))));
        });
        dc.appendChild(tb);
        nodes.push(dc);
        nodes.push(h('div', { id: 'dev-editor' }));
        page(t('nav_devices'), nodes);
      });
  };

  // The frame reports its version as "2.4 (7)"; the number in brackets is what updates compare.
  function appVersionCell(version, publishedCode) {
    var m = /\((\d+)\)\s*$/.exec(version || '');
    if (!m) return h('span', { class: 'muted' }, version || '—');
    var outdated = publishedCode != null && Number(m[1]) < publishedCode;
    return h('span', null, version + ' ', h('span', { class: 'pill ' + (outdated ? 'warn' : 'ok') }, outdated ? t('upd_outdated') : t('upd_ok')));
  }

  function deviceEditor(id, albums, global) {
    return api('GET', '/api/v1/admin/devices/' + id).then(function (d) {
      var c = d.config;
      var box = document.getElementById('dev-editor');
      clear(box);
      var name = { name: d.name };
      var albumOpts = [['', t('no_album')]].concat(albums.map(function (a) { return [a.id, a.name + ' (' + a.photos + ')']; }));
      var views = ['home', 'calendar', 'photos', 'chores', 'house', 'cameras', 'shopping', 'menu', 'music', 'settings'].map(function (k) { return [k, t('scr_' + k)]; });
      var haEnts = h('input', { value: c.presence.ha_entities.join(', '), placeholder: 'binary_sensor.pasillo_movimiento, ...' });
      haEnts.addEventListener('input', function () { c.presence.ha_entities = haEnts.value.split(',').map(function (x) { return x.trim(); }).filter(Boolean); });
      var widgetsSel = h('div', { class: 'row tight' });
      ['time', 'date', 'weather', 'calendar', 'tasks', 'people'].forEach(function (w) {
        var el = h('input', { type: 'checkbox', checked: c.photos.widgets.indexOf(w) >= 0 });
        el.addEventListener('change', function () {
          c.photos.widgets = c.photos.widgets.filter(function (x) { return x !== w; });
          if (el.checked) c.photos.widgets.push(w);
        });
        widgetsSel.appendChild(h('label', { class: 'chk' }, el, t('wg_' + w)));
      });
      var peopleSel = h('div', { class: 'row tight' });
      global.people.forEach(function (p) {
        var el = h('input', { type: 'checkbox', checked: c.layout.person_ids.indexOf(p.id) >= 0 });
        el.addEventListener('change', function () {
          c.layout.person_ids = c.layout.person_ids.filter(function (x) { return x !== p.id; });
          if (el.checked) c.layout.person_ids.push(p.id);
        });
        peopleSel.appendChild(h('label', { class: 'chk' }, el, p.name));
      });
      box.appendChild(h('div', { class: 'card' },
        h('h3', null, d.name + ' · ' + t('device_id') + ' ' + d.id),
        h('p', { class: 'muted' }, [t('ip') + ': ' + (d.last_ip || '—'), t('app_version') + ': ' + (d.app_version || '—'), t('version_cfg') + ': ' + d.config_version].join(' · ')),
        h('div', { class: 'row tight' },
          btn(t('command_wake'), function () { return api('POST', '/api/v1/admin/devices/' + id + '/command', { type: 'wake' }); }),
          btn(t('command_sleep'), function () { return api('POST', '/api/v1/admin/devices/' + id + '/command', { type: 'sleep' }); }),
          btn(t('command_reload'), function () { return api('POST', '/api/v1/admin/devices/' + id + '/command', { type: 'reload' }); }),
          btn(t('command_identify'), function () { return api('POST', '/api/v1/admin/devices/' + id + '/command', { type: 'identify' }); }),
          btn(t('command_update'), function () { return api('POST', '/api/v1/admin/devices/' + id + '/command', { type: 'update' }).then(function () { flash(box, 'ok', t('upd_cmd_sent')); }); }),
          btn(t('revoke'), function () { if (!confirm(t('revoke_confirm'))) return; return api('DELETE', '/api/v1/admin/devices/' + id).then(function () { go('devices'); }); }, 'bad')),
        h('p'),
        h('div', { class: 'row' }, input(name, 'name', t('name')), input(c, 'room', t('room')),
          select(c, 'language', t('language'), [['inherit', t('inherit')], ['es-ES', 'Español (España)'], ['en', 'English']])),
        h('h3', null, t('display')),
        h('div', { class: 'row' },
          select(c, 'display.brightness_mode', t('brightness_mode'), [['automatic', t('automatic')], ['manual', t('manual')], ['always_on', t('always_on')]]),
          input(c, 'display.brightness_min', t('brightness_min'), { type: 'number', min: 1, max: 100 }),
          input(c, 'display.brightness_max', t('brightness_max'), { type: 'number', min: 1, max: 100 }),
          input(c, 'display.inactivity_timeout', t('inactivity_timeout'), { type: 'number', min: 10 }),
          select(c, 'display.screen_off', t('screen_off'), [['never', t('never_off')], ['black', t('black')], ['off', t('off')]])),
        h('div', { class: 'row' }, check(c, 'display.night_mode', t('night_mode')), input(c, 'display.night_start', t('night_start'), { type: 'time' }),
          input(c, 'display.night_end', t('night_end'), { type: 'time' }), input(c, 'display.night_brightness', t('night_brightness'), { type: 'number', min: 0, max: 100 }),
          color(c, 'display.night_color', t('night_color'))),
        h('h3', null, t('presence')),
        h('div', { class: 'row' }, check(c, 'presence.enabled', t('enabled')),
          select(c, 'presence.provider', t('provider'), [['light_sensor', t('light_sensor')], ['homeassistant', t('homeassistant')], ['combined', t('combined')], ['none', t('none')]]),
          select(c, 'presence.sensitivity', t('sensitivity'), [['low', t('low')], ['medium', t('medium')], ['high', t('high')]])),
        h('div', { class: 'row' }, input(c, 'presence.min_abs_lux', t('min_abs_lux'), { type: 'number', step: 0.5 }),
          input(c, 'presence.min_rel_change', t('min_rel_change'), { type: 'number', step: 0.05 }),
          input(c, 'presence.min_event_gap_s', t('min_gap'), { type: 'number', step: 0.5 }),
          input(c, 'presence.activity_hold_s', t('hold'), { type: 'number' }),
          input(c, 'presence.ha_hold_seconds', t('ha_hold'), { type: 'number' })),
        h('div', { class: 'row' }, check(c, 'presence.sleep_on_lights_off', t('sleep_on_lights_off')), input(c, 'presence.lights_off_lux', t('lights_off_lux'), { type: 'number', min: 1, max: 50 })),
        h('p', { class: 'muted' }, t('lights_off_help')),
        h('div', null, h('label', null, t('ha_entities')), haEnts),
        h('h3', null, t('photos_cfg')),
        h('div', { class: 'row' }, check(c, 'photos.enabled', t('enabled')), select(c, 'photos.album_id', t('album'), albumOpts, { nullable: true }),
          input(c, 'photos.interval_s', t('interval'), { type: 'number', min: 5 }),
          select(c, 'photos.order', t('order'), [['random', t('random')], ['chronological', t('chronological')]]),
          select(c, 'photos.fit', t('fit'), [['cover', t('cover')], ['contain', t('contain')]]),
          input(c, 'photos.cache_limit', t('cache_limit'), { type: 'number', min: 10, max: 400 })),
        h('div', { class: 'row' }, color(c, 'photos.text_color', t('text_color')),
          select(c, 'photos.transition', t('transition'), [['fade', t('tr_fade')], ['none', t('tr_none')]])),
        check(c, 'photos.show_overlay', t('overlay')),
        h('label', null, t('widgets_h')), widgetsSel, h('p', { class: 'muted' }, t('widgets_help')),
        h('h3', null, t('sounds_h')),
        h('div', { class: 'row' }, input(c, 'sounds.volume', t('sounds_volume'), { type: 'number', min: 0, max: 100 }),
          check(c, 'sounds.chime.enabled', t('chime_enabled')),
          select(c, 'sounds.chime.every', t('chime_every'), [['hour', t('ev_hour')], ['half', t('ev_half')]]),
          select(c, 'sounds.chime.sound', t('chime_sound'), [['chime', t('snd_chime')], ['bell', t('snd_bell')], ['soft', t('snd_soft')], ['speak', t('snd_speak')]])),
        h('div', { class: 'row' }, check(c, 'sounds.chime.quiet', t('chime_quiet')), input(c, 'sounds.chime.quiet_start', t('quiet_start'), { type: 'time' }),
          input(c, 'sounds.chime.quiet_end', t('quiet_end'), { type: 'time' })),
        h('div', { class: 'row tight' }, btn(t('test_alert'), function () {
          return api('POST', '/api/v1/admin/devices/' + id + '/trigger', { action: 'alert', message: t('test_msg'), speak: true, sound: 'bell', duration_s: 10 }).then(function () { flash(box, 'ok', t('al_tested')); });
        })),
        h('h3', null, t('layout')),
        h('div', { class: 'row' }, select(c, 'layout.default_view', t('default_view'), views),
          select(c, 'layout.calendar_mode', t('calendar_mode'), [['day', t('cal_mode_day')], ['3day', t('cal_mode_3day')], ['week', t('cal_mode_week')], ['month', t('cal_mode_month')]]),
          input(c, 'layout.ambient_after_s', t('ambient_after'), { type: 'number', min: 15 }),
          input(c, 'layout.home_after_s', t('home_after'), { type: 'number', min: 10 })),
        peopleSel,
        h('p', { class: 'muted' }, t('calendar_mode_help')),
        btn(t('save'), function () {
          return api('PUT', '/api/v1/admin/devices/' + id, { name: name.name, config: c }).then(function () { flash(box, 'ok', t('saved')); });
        }, 'pri')));
      box.scrollIntoView({ behavior: 'smooth' });
    });
  }

  /* ---- app updates */
  function fmtSize(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.round(n / 1024) + ' KB'; }

  VIEWS.updates = function () {
    return api('GET', '/api/v1/admin/updates').then(function (ov) {
      var box = h('div');
      var mode = { mode: ov.mode };
      var notes = h('input', { placeholder: t('upd_notes'), maxlength: 500 });
      var file = h('input', { type: 'file', accept: '.apk,application/vnd.android.package-archive', style: null });
      file.style.display = 'none';
      var drop = h('div', { class: 'drop', tabindex: 0 }, t('upd_drop'));
      var progress = h('p', { class: 'muted' });
      function send(f) {
        if (!f) return;
        progress.textContent = t('uploading') + ' ' + f.name + ' (' + fmtSize(f.size) + ')…';
        api('POST', '/api/v1/admin/updates?filename=' + encodeURIComponent(f.name) + '&notes=' + encodeURIComponent(notes.value.trim()), f, { raw: true })
          .then(function (r) { flash(box, r.created ? 'ok' : 'err', r.created ? t('upd_created') : t('upd_exists')); return VIEWS.updates(); })
          .catch(function (e) { progress.textContent = ''; fail(e); });
      }
      drop.addEventListener('click', function () { file.click(); });
      ['dragenter', 'dragover'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.add('over'); }); });
      ['dragleave', 'drop'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.remove('over'); }); });
      drop.addEventListener('drop', function (ev) { send(ev.dataTransfer.files[0]); });
      file.addEventListener('change', function () { send(file.files[0]); });

      var table = h('table', null, h('tr', null, h('th', null, t('upd_version_col')), h('th', null, t('status')), h('th', null, t('upd_uploaded')), h('th', null, ''), h('th', null, '')));
      ov.releases.forEach(function (r) {
        var live = ov.published === r.version_code;
        table.appendChild(h('tr', null,
          h('td', null, h('b', null, r.version_name), ' ', h('span', { class: 'muted' }, '(' + r.version_code + ') · ' + fmtSize(r.size)), r.notes ? h('div', { class: 'muted' }, r.notes) : null,
            h('div', { class: 'muted' }, r.cert_sha256 ? t('upd_cert') + ' ' + r.cert_sha256.slice(0, 12) + '…' : '')),
          h('td', null, h('span', { class: 'pill ' + (live ? 'ok' : '') }, live ? t('upd_published') : t('upd_draft'))),
          h('td', { class: 'muted' }, new Date(r.uploaded_at * 1000).toLocaleString(lang === 'es' ? 'es-ES' : 'en-GB')),
          h('td', null, live
            ? btn(t('upd_unpublish'), function () { return api('POST', '/api/v1/admin/updates/unpublish').then(function () { return VIEWS.updates(); }); })
            : btn(t('upd_publish'), function () { if (!confirm(t('upd_publish_confirm'))) return; return api('POST', '/api/v1/admin/updates/' + r.version_code + '/publish').then(function () { return VIEWS.updates(); }); }, 'pri')),
          h('td', null, live ? null : btn(t('delete'), function () { if (!confirm(t('upd_delete_confirm'))) return; return api('DELETE', '/api/v1/admin/updates/' + r.version_code).then(function () { return VIEWS.updates(); }); }, 'bad'))));
      });
      page(t('nav_updates'), box);
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('upd_mode_h')),
        h('div', { class: 'row' }, select(mode, 'mode', t('upd_mode'), [['off', t('upd_mode_off')], ['notify', t('upd_mode_notify')], ['auto', t('upd_mode_auto')]]),
          h('div', { class: 'row tight' }, btn(t('save'), function () {
            return api('PUT', '/api/v1/admin/updates/settings', { mode: mode.mode }).then(function () { flash(box, 'ok', t('saved')); });
          }, 'pri'))),
        h('p', { class: 'muted' }, t('upd_mode_help'))));
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('upd_upload_title')), h('p', { class: 'muted' }, t('upd_help')), h('div', { class: 'row' }, h('div', null, h('label', null, t('upd_notes')), notes)), drop, file, progress));
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('upd_releases')), ov.releases.length ? table : h('p', { class: 'muted' }, t('upd_none'))));
    });
  };

  /* ---- photos */
  VIEWS.photos = function () {
    return api('GET', '/api/v1/admin/albums').then(function (albums) {
      var sel = state.album && albums.some(function (a) { return a.id === state.album; }) ? state.album : (albums[0] && albums[0].id);
      state.album = sel;
      var nodes = [];
      var nameIn = h('input', { placeholder: t('new_album'), maxlength: 100 });
      nodes.push(h('div', { class: 'card' }, h('div', { class: 'row' }, h('div', null, h('label', null, t('albums')), albumSelect(albums, sel)),
        h('div', null, h('label', null, t('new_album')), nameIn),
        h('div', { class: 'row tight' }, btn(t('create'), function () {
          if (!nameIn.value.trim()) return;
          return api('POST', '/api/v1/admin/albums', { name: nameIn.value.trim() }).then(function (a) { state.album = a.id; go('photos'); });
        }, 'pri')))));
      var holder = h('div');
      nodes.push(holder);
      page(t('nav_photos'), nodes);
      if (sel) return renderAlbum(holder, albums.filter(function (a) { return a.id === sel; })[0]);
    });
  };
  function albumSelect(albums, sel) {
    var el = h('select');
    albums.forEach(function (a) { el.appendChild(h('option', { value: a.id, selected: a.id === sel }, a.name + ' (' + a.photos + ')')); });
    el.addEventListener('change', function () { state.album = el.value; go('photos'); });
    return el;
  }
  function renderAlbum(holder, album) {
    return api('GET', '/api/v1/admin/albums/' + album.id + '/photos').then(function (photos) {
      clear(holder);
      var file = h('input', { type: 'file', multiple: true, accept: 'image/*,.heic,.heif', style: null });
      file.style.display = 'none';
      var drop = h('div', { class: 'drop', tabindex: 0 }, t('drop_here'));
      var progress = h('p', { class: 'muted' });
      drop.addEventListener('click', function () { file.click(); });
      ['dragenter', 'dragover'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.add('over'); }); });
      ['dragleave', 'drop'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.remove('over'); }); });
      drop.addEventListener('drop', function (ev) { uploadFiles(ev.dataTransfer.files); });
      file.addEventListener('change', function () { uploadFiles(file.files); });
      function uploadFiles(list) {
        var files = Array.prototype.slice.call(list), done = 0, dup = 0, errors = [];
        function next() {
          var f = files.shift();
          if (!f) {
            progress.textContent = '';
            if (errors.length) flash(holder, 'err', errors.join(' · '));
            if (dup) flash(holder, 'ok', dup + ' ' + t('duplicates'));
            return renderAlbum(holder, album);
          }
          progress.textContent = t('uploading') + ' ' + (done + 1) + ' ' + t('of') + ' ' + (done + 1 + files.length) + ' · ' + f.name;
          return api('POST', '/api/v1/admin/albums/' + album.id + '/photos?filename=' + encodeURIComponent(f.name), f, { raw: true })
            .then(function (r) { if (!r.created) dup++; })
            .catch(function (e) { errors.push(f.name + ': ' + e.message); })
            .then(function () { done++; return next(); });
        }
        next();
      }
      var ren = h('input', { value: album.name, maxlength: 100 });
      holder.appendChild(h('div', { class: 'card' },
        h('div', { class: 'row' }, h('div', null, h('label', null, t('name')), ren),
          h('div', { class: 'row tight' }, btn(t('rename'), function () { return api('PUT', '/api/v1/admin/albums/' + album.id, { name: ren.value.trim() }).then(function () { go('photos'); }); }),
            btn(t('delete'), function () { if (!confirm(t('delete_album_confirm'))) return; return api('DELETE', '/api/v1/admin/albums/' + album.id).then(function () { state.album = null; go('photos'); }); }, 'bad'))),
        h('p'), drop, file, progress));
      var grid = h('div', { class: 'grid' });
      photos.forEach(function (p) {
        var cap = h('div', { class: 'cap' }, p.caption || '');
        var del = h('button', { class: 'btn bad', title: t('delete') }, '✕');
        del.addEventListener('click', function () {
          if (!confirm(t('delete_photo_confirm'))) return;
          api('DELETE', '/api/v1/admin/photos/' + p.id).then(function () { renderAlbum(holder, album); }).catch(fail);
        });
        var img = h('img', { src: '/api/v1/admin/photos/' + p.id + '/thumb', loading: 'lazy', alt: p.caption || '' });
        img.addEventListener('dblclick', function () {
          var c = prompt(t('caption'), p.caption || '');
          if (c === null) return;
          api('PATCH', '/api/v1/admin/photos/' + p.id, { caption: c }).then(function () { renderAlbum(holder, album); }).catch(fail);
        });
        grid.appendChild(h('div', { class: 'thumb' }, img, del, p.caption ? cap : null));
      });
      holder.appendChild(h('div', { class: 'card' }, h('h3', null, photos.length + ' ' + t('photos_n')), grid));
    });
  }

  /* ---- config-backed views */
  function loadConfig() { return api('GET', '/api/v1/admin/config'); }
  function saveConfig(cfg, container) {
    return api('PUT', '/api/v1/admin/config', cfg).then(function () { flash(container || main, 'ok', t('saved')); });
  }
  function slug(s) { return (s || 'x').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30) || 'x'; }

  var TZS = ['Europe/Madrid', 'Atlantic/Canary', 'Europe/London', 'Europe/Lisbon', 'Europe/Paris', 'Europe/Berlin', 'America/Mexico_City', 'America/Bogota', 'America/Argentina/Buenos_Aires', 'America/New_York', 'UTC'];

  VIEWS.general = function () {
    return loadConfig().then(function (r) {
      var cfg = r.config;
      if (!cfg.general.location) cfg.general.location = { latitude: null, longitude: null, name: '' };
      var tzs = TZS.indexOf(cfg.general.timezone) < 0 ? [cfg.general.timezone].concat(TZS) : TZS;
      var peopleBox = h('div');
      function drawPeople() {
        clear(peopleBox);
        cfg.people.forEach(function (p, i) {
          peopleBox.appendChild(h('div', { class: 'row' }, input(p, 'name', t('name')), input(p, 'color', t('color'), { type: 'color' }), input(p, 'ha_person', t('ha_person'), { nullable: true, placeholder: 'person.ana' }),
            h('div', { class: 'row tight' }, btn(t('delete'), function () { cfg.people.splice(i, 1); drawPeople(); }, 'bad'))));
        });
      }
      drawPeople();
      var box = h('div');
      page(t('nav_general'), box);
      box.appendChild(h('div', { class: 'card' },
        h('div', { class: 'row' }, select(cfg, 'general.language', t('language'), [['es-ES', 'Español (España)'], ['en', 'English']]),
          select(cfg, 'general.timezone', t('timezone'), tzs.map(function (z) { return [z, z]; }))),
        h('h3', null, t('location')),
        h('div', { class: 'row' }, input(cfg, 'general.location.name', t('place_name')), input(cfg, 'general.location.latitude', t('latitude'), { type: 'number', step: 'any', nullable: true }),
          input(cfg, 'general.location.longitude', t('longitude'), { type: 'number', step: 'any', nullable: true }))));
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('people')), h('p', { class: 'muted' }, t('people_help')), peopleBox, h('p'),
        btn(t('add_person'), function () { cfg.people.push({ id: 'p' + Math.random().toString(36).slice(2, 7), name: '', color: '#2D5BFF', ha_person: null }); drawPeople(); })));
      box.appendChild(btn(t('save'), function () {
        var g = cfg.general.location;
        if (!g.name && g.latitude == null && g.longitude == null) cfg.general.location = null;
        cfg.people.forEach(function (p) { if (!p.id || !/^[a-z0-9][a-z0-9-]*$/.test(p.id)) p.id = slug(p.name); if (!p.ha_person) p.ha_person = null; });
        return saveConfig(cfg, box).then(function () { return VIEWS.general(); });
      }, 'pri'));
    });
  };

  var DEFAULT_ORDER = ['calendar', 'photos', 'chores', 'house', 'cameras', 'shopping', 'menu', 'music'];
  function normalizeOrder(order) {
    var seen = (order || []).filter(function (k, i, a) { return DEFAULT_ORDER.indexOf(k) >= 0 && a.indexOf(k) === i; });
    return seen.concat(DEFAULT_ORDER.filter(function (k) { return seen.indexOf(k) < 0; }));
  }

  VIEWS.screens = function () {
    return loadConfig().then(function (r) {
      var cfg = r.config;
      var order = normalizeOrder(cfg.general.nav_order);
      var list = h('div', { class: 'order' });
      var box = h('div');
      function fixed(key, text) {
        return h('div', { class: 'item fixed' }, h('span', { class: 'num' }, icon('lock')), h('span', { class: 'name' }, t('scr_' + key)), h('span', { class: 'muted' }, text));
      }
      function move(i, d) {
        var j = i + d;
        if (j < 0 || j >= order.length) return;
        var x = order[i]; order[i] = order[j]; order[j] = x;
        draw();
      }
      function draw() {
        clear(list);
        list.appendChild(fixed('home', t('fixed_first')));
        order.forEach(function (k, i) {
          var up = h('button', { class: 'btn', type: 'button', title: t('move_up'), 'aria-label': t('move_up'), disabled: i === 0, onclick: function () { move(i, -1); } }, icon('up'));
          var down = h('button', { class: 'btn', type: 'button', title: t('move_down'), 'aria-label': t('move_down'), disabled: i === order.length - 1, onclick: function () { move(i, 1); } }, icon('down'));
          list.appendChild(h('div', { class: 'item' }, h('span', { class: 'num' }, String(i + 2)), h('span', { class: 'name' }, t('scr_' + k)), up, down));
        });
        list.appendChild(fixed('settings', t('fixed_last')));
      }
      draw();
      page(t('nav_screens'), box);
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('screens_title')), h('p', { class: 'muted' }, t('screens_help')), list,
        h('div', { class: 'actions' },
          btn(t('save'), function () { cfg.general.nav_order = order.slice(); return saveConfig(cfg, box); }, 'pri'),
          btn(t('reset_order'), function () { order = DEFAULT_ORDER.slice(); draw(); }))));
    });
  };

  VIEWS.calendars = function () {
    return loadConfig().then(function (r) {
      var cfg = r.config, secrets = r.secrets.calendars;
      var list = h('div');
      var box = h('div');
      page(t('nav_calendars'), box);
      function draw() {
        clear(list);
        cfg.calendars.forEach(function (c, i) {
          var pw = h('input', { type: 'password', autocomplete: 'new-password', placeholder: secrets[c.id] ? '••••••••' : '' });
          var people = h('div', { class: 'row tight' });
          cfg.people.forEach(function (p) {
            var el = h('input', { type: 'checkbox', checked: c.person_ids.indexOf(p.id) >= 0 });
            el.addEventListener('change', function () { c.person_ids = c.person_ids.filter(function (x) { return x !== p.id; }); if (el.checked) c.person_ids.push(p.id); });
            people.appendChild(h('label', { class: 'chk' }, el, p.name));
          });
          list.appendChild(h('div', { class: 'card' },
            h('div', { class: 'row' }, input(c, 'name', t('name')), select(c, 'type', t('type'), [['ics', 'ICS / webcal'], ['caldav', 'CalDAV']]), input(c, 'refresh_minutes', t('refresh_min'), { type: 'number', min: 5 })),
            h('div', { class: 'row' }, input(c, 'url', t('url'), { placeholder: 'https://… / webcal://…' })),
            h('div', { class: 'row' }, input(c, 'username', t('calendar_user')), h('div', null, h('label', null, t('calendar_pw')), pw), input(c, 'calendar_name', t('calendar_name'))),
            h('label', null, t('calendar_people')), people, h('p', { class: 'muted' }, t('calendar_tag_help')), check(c, 'enabled', t('enabled')), h('p'),
            h('div', { class: 'row tight' },
              btn(t('save'), function () {
                return saveConfig(cfg, box).then(function () { return pw.value ? api('PUT', '/api/v1/admin/calendars/' + c.id + '/password', { password: pw.value }) : null; })
                  .then(function () { pw.value = ''; });
              }, 'pri'),
              btn(t('sync_now'), function () { return api('POST', '/api/v1/admin/calendars/' + c.id + '/sync').then(function (s) { flash(box, 'ok', s.detail || t('saved')); }); }),
              btn(t('delete'), function () { cfg.calendars.splice(i, 1); return saveConfig(cfg, box).then(function () { return VIEWS.calendars(); }); }, 'bad'))));
        });
      }
      draw();
      box.appendChild(list);
      box.appendChild(btn(t('add_calendar'), function () {
        cfg.calendars.push({ id: 'cal-' + Math.random().toString(36).slice(2, 7), name: 'Calendario', type: 'ics', url: '', username: '', calendar_name: '', person_ids: [], enabled: true, refresh_minutes: 15 });
        draw();
      }));
    });
  };

  var ICON_NAMES = ['tasks', 'broom', 'trash', 'bed', 'shirt', 'dish', 'utensils', 'bath', 'book', 'paw', 'plant', 'car', 'cart', 'box', 'door', 'window', 'bulb', 'power', 'bolt', 'tv', 'film', 'music',
    'blinds', 'garage', 'lock', 'unlock', 'thermo', 'camera', 'drop', 'bell', 'clock', 'sunrise', 'sun', 'moon', 'away', 'home', 'heart', 'star', 'person', 'play', 'cloud'];
  var ICON_LABELS = { es: { tasks: 'Tarea', broom: 'Escoba', trash: 'Basura', bed: 'Cama', shirt: 'Ropa', dish: 'Platos', utensils: 'Cocina', bath: 'Baño', book: 'Libro / deberes', paw: 'Mascota', plant: 'Plantas', car: 'Coche', cart: 'Compra', box: 'Caja', door: 'Puerta', window: 'Ventana', bulb: 'Luz', power: 'Encendido', bolt: 'Energía', tv: 'Televisión', film: 'Cine', music: 'Música', blinds: 'Persiana', garage: 'Garaje', lock: 'Cerrado', unlock: 'Abierto', thermo: 'Temperatura', camera: 'Cámara', drop: 'Agua', bell: 'Timbre', clock: 'Reloj', sunrise: 'Amanecer', sun: 'Sol', moon: 'Luna', away: 'Salir', home: 'Casa', heart: 'Corazón', star: 'Estrella', person: 'Persona', play: 'Reproducir', cloud: 'Nube' } };
  function iconSelect(obj, path, label, allowNone) {
    var opts = (allowNone ? [['', '—']] : []).concat(ICON_NAMES.map(function (n) { return [n, (lang === 'es' && ICON_LABELS.es[n]) || n]; }));
    return select(obj, path, label, opts);
  }
  function peoplePicker(cfg, arr) {
    var row = h('div', { class: 'row tight' });
    cfg.people.forEach(function (p) {
      var el = h('input', { type: 'checkbox', checked: arr.indexOf(p.id) >= 0 });
      el.addEventListener('change', function () { var i = arr.indexOf(p.id); if (i >= 0) arr.splice(i, 1); if (el.checked) arr.push(p.id); });
      row.appendChild(h('label', { class: 'chk' }, el, p.name));
    });
    return row;
  }

  function todayIso() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }

  VIEWS.chores = function () {
    return loadConfig().then(function (r) {
      var cfg = r.config, list = h('div'), box = h('div'), open = null;
      page(t('nav_chores'), box);
      box.appendChild(h('p', { class: 'muted' }, t('chores_help2')));

      function who(c) {
        var names = cfg.people.filter(function (p) { return c.person_ids.indexOf(p.id) >= 0; }).map(function (p) { return p.name; });
        return names.length ? names.join(', ') : t('ch_whole_house');
      }
      function when(c) {
        if (c.week_mode === 'once') return t('ch_due') + ' ' + dayLabel(c.start_date);
        var parts = [daysText(c.days)];
        if (c.week_mode === 'even') parts.push(t('ch_weeks_even'));
        else if (c.week_mode === 'odd') parts.push(t('ch_weeks_odd'));
        else if (c.week_mode === 'every') parts.push(t('ch_weeks_every', { n: c.every_weeks }));
        return parts.join(' · ');
      }
      function editor(c) {
        var once = c.week_mode === 'once';
        var kind = seg([['repeat', t('ch_kind_repeat')], ['once', t('ch_kind_once')]], once ? 'once' : 'repeat', function (k) {
          if (k === 'once') { c.week_mode = 'once'; if (!c.start_date) c.start_date = todayIso(); } else if (c.week_mode === 'once') c.week_mode = 'all';
          draw();
        });
        var mode = select(c, 'week_mode', t('week_mode'), [['all', t('wm_all')], ['even', t('wm_even')], ['odd', t('wm_odd')], ['every', t('wm_every')]]);
        mode.querySelector('select').addEventListener('change', function () {
          if (c.week_mode === 'every') { if (!c.start_date) c.start_date = todayIso(); if (!c.every_weeks) c.every_weeks = 2; }
          draw();
        });
        var quick = h('div', { class: 'row tight' },
          btn(t('ch_every_day'), function () { c.days = []; draw(); }), btn(t('ch_weekdays'), function () { c.days = [0, 1, 2, 3, 4]; draw(); }),
          btn(t('ch_weekend'), function () { c.days = [5, 6]; draw(); }));
        return h('div', { class: 'chedit' },
          h('div', { class: 'row' }, input(c, 'title', t('ch_what')), iconSelect(c, 'icon', t('icon'))),
          h('label', null, t('ch_who')), peoplePicker(cfg, c.person_ids), h('p', { class: 'muted' }, t('ch_who_help')),
          h('label', null, t('ch_when')), kind,
          once ? h('div', { class: 'row' }, input(c, 'start_date', t('ch_due'), { type: 'date' }), input(c, 'time', t('time_opt'), { type: 'time' })) : [
            h('label', null, t('chore_days')), dayChips(c.days), h('label', null, t('ch_quick')), quick,
            h('div', { class: 'row' }, mode,
              c.week_mode === 'every' ? input(c, 'every_weeks', t('every_weeks'), { type: 'number', min: 2, max: 12 }) : null,
              c.week_mode === 'every' ? input(c, 'start_date', t('start_week'), { type: 'date' }) : null,
              input(c, 'time', t('time_opt'), { type: 'time' })),
            h('p', { class: 'muted' }, t('week_help'))],
          once ? h('p', { class: 'muted' }, t('ch_once_help')) : null,
          h('div', { class: 'row tight' }, check(c, 'enabled', t('enabled'))));
      }
      function draw() {
        clear(list);
        if (!cfg.chores.length) list.appendChild(h('div', { class: 'empty' }, t('chores_none')));
        cfg.chores.forEach(function (c, i) {
          var isOpen = open === c.id;
          list.appendChild(h('div', { class: 'card chcard' + (c.enabled ? '' : ' off') + (c.week_mode === 'once' ? ' once' : '') },
            h('div', { class: 'chcard-h' },
              h('div', { class: 'chcard-t' },
                h('b', null, c.title || t('ch_untitled')),
                h('span', { class: 'muted' }, who(c) + ' · ' + when(c) + (c.time ? ' · ' + c.time : ''))),
              h('div', { class: 'chcard-a' },
                c.week_mode === 'once' ? h('span', { class: 'pill warn' }, t('ch_kind_once')) : null,
                c.enabled ? null : h('span', { class: 'pill' }, t('ch_paused')),
                btn(isOpen ? t('ch_close') : t('ch_edit'), function () { open = isOpen ? null : c.id; draw(); }),
                btn(t('delete'), function () { cfg.chores.splice(i, 1); draw(); }, 'bad'))),
            isOpen ? editor(c) : null));
        });
      }
      function blank(once) {
        var c = { id: 'c' + Math.random().toString(36).slice(2, 8), title: '', icon: 'tasks', person_ids: [], days: [], week_mode: once ? 'once' : 'all', every_weeks: 2, start_date: once ? todayIso() : '', time: '', enabled: true };
        cfg.chores.push(c); open = c.id; draw();
      }
      draw();
      box.appendChild(list);
      box.appendChild(h('div', { class: 'row tight' },
        btn(t('add_chore'), function () { blank(false); }), btn(t('ch_new_once'), function () { blank(true); }),
        btn(t('save'), function () {
          cfg.chores = cfg.chores.filter(function (c) { return c.title.trim(); });
          cfg.chores.forEach(function (c) {
            c.title = c.title.trim();
            if ((c.week_mode === 'once' || c.week_mode === 'every') && !c.start_date) c.start_date = todayIso();
          });
          return saveConfig(cfg, box).then(function () { return VIEWS.chores(); });
        }, 'pri')));
    });
  };

  VIEWS.alarms = function () {
    return Promise.all([loadConfig(), api('GET', '/api/v1/admin/devices')]).then(function (rs) {
      var cfg = rs[0].config, devices = rs[1], list = h('div'), box = h('div'), open = null;
      var SOUNDS = [['melody', t('snd_melody')], ['chime', t('snd_chime')], ['bell', t('snd_bell')], ['soft', t('snd_soft')], ['beep', t('snd_beep')], ['none', t('al_sound_none')]];
      page(t('nav_alarms'), box);
      function soundName(v) { var f = SOUNDS.filter(function (o) { return o[0] === v; })[0]; return f ? f[1] : v; }
      function frames(a) {
        if (!a.device_ids.length) return t('al_all_frames');
        return devices.filter(function (d) { return a.device_ids.indexOf(d.id) >= 0; }).map(function (d) { return d.name; }).join(', ');
      }
      function framePicker(a) {
        var row = h('div', { class: 'row tight' });
        devices.forEach(function (d) {
          var el = h('input', { type: 'checkbox', checked: a.device_ids.indexOf(d.id) >= 0 });
          el.addEventListener('change', function () { var k = a.device_ids.indexOf(d.id); if (k >= 0) a.device_ids.splice(k, 1); if (el.checked) a.device_ids.push(d.id); });
          row.appendChild(h('label', { class: 'chk' }, el, d.name));
        });
        return row;
      }
      function tryIt(a) {
        var targets = devices.filter(function (d) { return !a.device_ids.length || a.device_ids.indexOf(d.id) >= 0; });
        return Promise.all(targets.map(function (d) {
          return api('POST', '/api/v1/admin/devices/' + d.id + '/trigger', { action: 'alert', message: a.message || a.name || t('test_msg'), speak: a.speak, sound: a.sound, volume: a.volume, duration_s: 15 });
        })).then(function () { flash(box, 'ok', t('al_tested')); });
      }
      function editor(a) {
        var byDate = !!a.date;
        var kind = seg([['days', t('al_days')], ['date', t('al_date')]], byDate ? 'date' : 'days', function (k) {
          if (k === 'date') { if (!a.date) a.date = todayIso(); } else a.date = '';
          draw();
        });
        return h('div', { class: 'chedit' },
          h('div', { class: 'row' }, input(a, 'name', t('al_name')), input(a, 'time', t('al_time'), { type: 'time' })),
          kind,
          byDate ? h('div', { class: 'row' }, input(a, 'date', t('al_date'), { type: 'date' })) : dayChips(a.days),
          h('div', { class: 'row' }, select(a, 'sound', t('al_sound'), SOUNDS), input(a, 'volume', t('al_volume'), { type: 'number', min: 1, max: 100 })),
          h('div', null, h('label', null, t('al_message')), (function () { var el = h('input', { value: a.message, maxlength: 200 }); el.addEventListener('input', function () { a.message = el.value; }); return el; })()),
          check(a, 'speak', t('al_speak')), h('p', { class: 'muted' }, t('al_tts_help')),
          h('div', { class: 'row' }, input(a, 'duration_s', t('al_duration'), { type: 'number', min: 5, max: 900 }), input(a, 'snooze_min', t('al_snooze'), { type: 'number', min: 0, max: 60 })),
          h('label', null, t('al_frames')), framePicker(a), h('p', { class: 'muted' }, t('al_frames_help')),
          h('div', { class: 'row tight' }, btn(t('al_test'), function () { return tryIt(a); })));
      }
      function draw() {
        clear(list);
        if (!cfg.alarms.length) list.appendChild(h('div', { class: 'empty' }, t('al_none')));
        cfg.alarms.forEach(function (a, i) {
          var isOpen = open === a.id;
          var when = a.date ? t('al_once_on', { d: dayLabel(a.date) }) : daysText(a.days);
          list.appendChild(h('div', { class: 'card chcard' + (a.enabled ? '' : ' off') },
            h('div', { class: 'chcard-h' },
              h('div', { class: 'alarm-time' }, a.time),
              h('div', { class: 'chcard-t' },
                h('b', null, a.name || a.message || t('al_untitled')),
                h('span', { class: 'muted' }, [when, soundName(a.sound), a.speak ? t('al_speak') : '', frames(a)].filter(Boolean).join(' · '))),
              h('div', { class: 'chcard-a' },
                a.enabled ? null : h('span', { class: 'pill' }, t('al_off')),
                btn(isOpen ? t('al_close') : t('al_edit'), function () { open = isOpen ? null : a.id; draw(); }),
                btn(t('delete'), function () { cfg.alarms.splice(i, 1); draw(); }, 'bad'))),
            isOpen ? h('div', null, editor(a), h('div', { class: 'row tight' }, check(a, 'enabled', t('enabled')))) : null));
        });
      }
      draw();
      box.appendChild(list);
      box.appendChild(h('div', { class: 'row tight' },
        btn(t('al_add'), function () {
          var a = { id: 'a' + Math.random().toString(36).slice(2, 8), name: '', time: '07:00', days: [], date: '', enabled: true, sound: 'melody', message: '', speak: false, volume: 80, duration_s: 60, snooze_min: 5, device_ids: [] };
          cfg.alarms.push(a); open = a.id; draw();
        }),
        btn(t('save'), function () {
          cfg.alarms.forEach(function (a) { if (a.sound === 'none' && !a.message.trim()) a.sound = 'melody'; if (a.date && !/^\d{4}-\d{2}-\d{2}$/.test(a.date)) a.date = ''; });
          return saveConfig(cfg, box).then(function () { return VIEWS.alarms(); });
        }, 'pri')));
    });
  };

  VIEWS.cameras = function () {
    return Promise.all([loadConfig(), api('GET', '/api/v1/admin/homeassistant/entities?domain=camera').catch(function () { return []; })]).then(function (rs) {
      var cfg = rs[0].config, haCams = rs[1], detected = [], box = h('div'), list = h('div');
      page(t('nav_cameras'), box);
      box.appendChild(h('p', { class: 'muted' }, t('cameras_help')));
      var detectMsg = h('span', { class: 'muted' });
      function persist() {
        cfg.cameras.forEach(function (c) {
          c.fps = Number(c.fps) || 5;
          c.name = c.name.trim() || c.frigate_camera || c.ha_entity || 'Cámara';
          if (c.source === 'ha' && c.ha_entity && cfg.homeassistant.authorized_entities.indexOf(c.ha_entity) < 0) cfg.homeassistant.authorized_entities.push(c.ha_entity);
        });
        return saveConfig(cfg, box);
      }
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('frigate')),
        h('div', { class: 'row' }, input(cfg, 'frigate.url', t('frigate_url'), { placeholder: 'http://192.168.1.10:5000' }), check(cfg, 'frigate.verify_tls', t('verify_tls'))), h('p'),
        h('div', { class: 'row tight' }, btn(t('save'), persist, 'pri'),
          btn(t('detect'), function () {
            return persist().then(function () { return api('GET', '/api/v1/admin/frigate/cameras'); }).then(function (names) {
              detected = names; detectMsg.textContent = t('detected', { n: names.length }); draw();
            });
          }), detectMsg)));
      function sourceField(c) {
        if (c.source === 'ha') {
          var opts = [['', '—']].concat(haCams.map(function (e) { return [e.entity_id, (e.name || e.entity_id) + ' (' + e.entity_id + ')']; }));
          if (c.ha_entity && !haCams.some(function (e) { return e.entity_id === c.ha_entity; })) opts.push([c.ha_entity, c.ha_entity]);
          return select(c, 'ha_entity', t('ha_camera'), opts, { nullable: true });
        }
        if (c.source === 'url') return input(c, 'url', t('src_url'), { placeholder: 'http://…/snapshot.jpg' });
        if (detected.length) {
          var names = detected.indexOf(c.frigate_camera) < 0 && c.frigate_camera ? [c.frigate_camera].concat(detected) : detected;
          return select(c, 'frigate_camera', t('frigate_camera'), [['', '—']].concat(names.map(function (n) { return [n, n]; })));
        }
        return input(c, 'frigate_camera', t('frigate_camera'), { placeholder: 'patio' });
      }
      function draw() {
        clear(list);
        cfg.cameras.forEach(function (c, i) {
          var preview = h('img', { alt: '', style: 'max-width:320px;border-radius:8px;display:none;margin-top:8px', src: '' });
          list.appendChild(h('div', { class: 'card' },
            h('div', { class: 'row' }, input(c, 'name', t('name')),
              (function () { var sel = select(c, 'source', t('source'), [['frigate', t('src_frigate')], ['ha', t('src_ha')], ['url', t('src_url')]]); sel.querySelector('select').addEventListener('change', draw); return sel; })(),
              sourceField(c), input(c, 'fps', t('fps'), { type: 'number', min: 1, max: 10 })),
            check(c, 'enabled', t('enabled')), h('p'),
            h('div', { class: 'row tight' },
              btn(t('preview'), function () {
                return persist().then(function () { preview.style.display = 'block'; preview.src = '/api/v1/admin/cameras/' + encodeURIComponent(c.id) + '/snapshot?t=' + Date.now(); });
              }),
              btn(t('delete'), function () { cfg.cameras.splice(i, 1); draw(); }, 'bad')), preview));
        });
      }
      draw();
      box.appendChild(list);
      box.appendChild(h('div', { class: 'row tight' },
        btn(t('add_camera'), function () { cfg.cameras.push({ id: 'cam-' + Math.random().toString(36).slice(2, 7), name: '', source: 'frigate', frigate_camera: '', ha_entity: null, url: '', fps: 5, enabled: true }); draw(); }),
        btn(t('save'), function () { return persist().then(function () { return VIEWS.cameras(); }); }, 'pri')));
    });
  };

  VIEWS.ha = function () {
    return Promise.all([loadConfig(), api('GET', '/api/v1/admin/status')]).then(function (rs) {
      var r = rs[0], st = rs[1].homeassistant, cfg = r.config, ha = cfg.homeassistant;
      var tokenIn = h('input', { type: 'password', autocomplete: 'off', placeholder: r.secrets.homeassistant_token ? '••••••••' : '' });
      var box = h('div');
      page(t('nav_ha'), box);
      var statusLine = h('p', null, h('span', { class: 'pill ' + (st.connected ? 'ok' : (st.enabled ? 'bad' : '')) }, st.connected ? t('connected') : t('disconnected')), ' ',
        r.secrets.homeassistant_token ? t('token_saved') : t('token_missing'), st.error ? ' · ' + st.error : '');
      box.appendChild(h('div', { class: 'card' }, statusLine,
        h('div', { class: 'row' }, check(ha, 'enabled', t('enabled')), input(ha, 'url', t('ha_url'), { placeholder: 'http://homeassistant.local:8123' }), check(ha, 'verify_tls', t('verify_tls'))),
        h('div', { class: 'row' }, h('div', null, h('label', null, t('ha_token')), tokenIn)),
        h('p'),
        h('div', { class: 'row tight' },
          btn(t('save'), function () {
            return saveConfig(cfg, box).then(function () { return tokenIn.value ? api('PUT', '/api/v1/admin/homeassistant/token', { token: tokenIn.value }) : null; })
              .then(function () { setTimeout(function () { VIEWS.ha().catch(fail); }, 1500); });
          }, 'pri'),
          btn(t('test_conn'), function () {
            var body = { url: ha.url, verify_tls: ha.verify_tls };
            if (tokenIn.value) body.token = tokenIn.value;
            return api('POST', '/api/v1/admin/homeassistant/test', body).then(function (x) { flash(box, 'ok', t('conn_ok', { v: x.version })); });
          }),
          btn(t('delete_token'), function () { return api('DELETE', '/api/v1/admin/homeassistant/token').then(function () { VIEWS.ha(); }); }, 'bad'))));
      var entBox = h('div', { class: 'card' }, h('h3', null, t('authorized')));
      box.appendChild(entBox);
      if (!st.connected) return;
      return api('GET', '/api/v1/admin/homeassistant/entities').then(function (ents) {
        var filter = h('input', { placeholder: t('filter') });
        var listEl = h('div', { class: 'ents' });
        function draw() {
          clear(listEl);
          var q = filter.value.toLowerCase();
          ents.filter(function (e) { return !q || e.entity_id.toLowerCase().indexOf(q) >= 0 || (e.name || '').toLowerCase().indexOf(q) >= 0; }).forEach(function (e) {
            var el = h('input', { type: 'checkbox', checked: ha.authorized_entities.indexOf(e.entity_id) >= 0 });
            var cust = h('div', { class: 'ents-cust' });
            function drawCust() {
              clear(cust);
              if (!el.checked || e.entity_id.indexOf('camera.') === 0 || e.entity_id.indexOf('sensor.') === 0 || e.entity_id.indexOf('binary_sensor.') === 0) return;
              var m = ha.entity_meta[e.entity_id] || (ha.entity_meta[e.entity_id] = { name: '', icon: '', color: '' });
              var clr = h('input', { type: 'color', value: m.color || '#2d5bff' });
              clr.addEventListener('input', function () { m.color = clr.value; });
              add(cust, h('div', { class: 'row' }, input(m, 'name', t('custom_name'), { placeholder: e.name || e.entity_id }), iconSelect(m, 'icon', t('icon'), true),
                h('div', null, h('label', null, t('color')), clr),
                h('div', { class: 'row tight' }, btn(t('clear'), function () { delete ha.entity_meta[e.entity_id]; drawCust(); }))));
            }
            el.addEventListener('change', function () {
              ha.authorized_entities = ha.authorized_entities.filter(function (x) { return x !== e.entity_id; });
              if (el.checked) ha.authorized_entities.push(e.entity_id);
              drawCust();
            });
            drawCust();
            listEl.appendChild(h('div', { class: 'ent' }, h('label', null, el, h('span', null, (e.name || e.entity_id)), h('small', null, e.entity_id + ' · ' + e.state)), cust));
          });
        }
        filter.addEventListener('input', draw);
        draw();
        add(entBox, [h('p', { class: 'muted' }, t('ha_custom_help')), filter, h('p'), listEl, h('p'), btn(t('save'), function () {
          Object.keys(ha.entity_meta).forEach(function (k) {
            var m = ha.entity_meta[k];
            if (ha.authorized_entities.indexOf(k) < 0 || (!m.name.trim() && !m.icon && !m.color)) delete ha.entity_meta[k];
            else { m.name = m.name.trim(); }
          });
          return saveConfig(cfg, box);
        }, 'pri')]);
      });
    });
  };

  VIEWS.shopping = function () {
    return Promise.all([loadConfig(), api('GET', '/api/v1/admin/homeassistant/entities?domain=todo').catch(function () { return []; })]).then(function (rs) {
      var cfg = rs[0].config, todos = rs[1];
      var opts = [['', '—']].concat(todos.map(function (e) { return [e.entity_id, (e.name || e.entity_id) + ' (' + e.entity_id + ')']; }));
      if (cfg.shopping.ha_entity && !todos.some(function (e) { return e.entity_id === cfg.shopping.ha_entity; })) opts.push([cfg.shopping.ha_entity, cfg.shopping.ha_entity]);
      var box = h('div');
      page(t('nav_shopping'), box);
      box.appendChild(h('div', { class: 'card' },
        h('div', { class: 'row' }, select(cfg, 'shopping.provider', t('shopping_provider'), [['local', t('local')], ['homeassistant', t('ha_list')]]),
          select(cfg, 'shopping.ha_entity', t('ha_list_entity'), opts, { nullable: true })),
        h('p', { class: 'muted' }, t('shopping_hint')), btn(t('save'), function () { return saveConfig(cfg, box); }, 'pri')));
    });
  };

  /* ---- light sensor diagnostics */
  VIEWS.sensor = function () {
    return Promise.all([api('GET', '/api/v1/admin/devices'), api('GET', '/api/v1/admin/recordings')]).then(function (rs) {
      var devices = rs[0], recs = rs[1];
      var box = h('div');
      page(t('nav_sensor'), box);
      if (!devices.length) return;
      var dev = devices.filter(function (d) { return d.id === state.sensorDev; })[0] || devices[0];
      state.sensorDev = dev.id;
      var sel = h('select');
      devices.forEach(function (d) { sel.appendChild(h('option', { value: d.id, selected: d.id === dev.id }, d.name)); });
      sel.addEventListener('change', function () { state.sensorDev = sel.value; go('sensor'); });
      var canvas = h('canvas', { class: 'chart', width: 1000, height: 220 });
      var now = h('b', null, '—');
      var recName = h('input', { placeholder: t('rec_name'), maxlength: 100 });
      var recState = { recording: false };
      box.appendChild(h('div', { class: 'card' }, h('div', { class: 'row' }, h('div', null, h('label', null, t('choose_device')), sel),
        h('div', null, h('label', null, t('lux_now')), now)), h('p'), canvas));
      var recBtns = h('div', { class: 'row tight' });
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('recording')), h('div', { class: 'row' }, h('div', null, h('label', null, t('rec_name')), recName), recBtns)));
      function drawBtns() {
        clear(recBtns);
        recBtns.appendChild(recState.recording
          ? btn(t('stop_rec'), function () { return api('POST', '/api/v1/admin/devices/' + dev.id + '/recording', { action: 'stop' }).then(function () { go('sensor'); }); }, 'bad')
          : btn(t('start_rec'), function () { return api('POST', '/api/v1/admin/devices/' + dev.id + '/recording', { action: 'start', name: recName.value }).then(function () { recState.recording = true; drawBtns(); }); }, 'pri'));
      }
      var rt = h('table', null, h('tr', null, h('th', null, t('name')), h('th', null, t('samples')), h('th', null, ''))); 
      recs.forEach(function (x) {
        rt.appendChild(h('tr', null, h('td', null, (x.name || x.id) + ' · ' + fmtDate(x.started_at)), h('td', null, String(x.samples)), h('td', null, h('a', { href: '/api/v1/admin/recordings/' + x.id + '/csv' }, t('download')))));
      });
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('recordings')), rt));
      function tick() {
        api('GET', '/api/v1/admin/devices/' + dev.id + '/telemetry').then(function (d) {
          recState.recording = d.recording; drawBtns();
          var s = d.samples || [];
          if (s.length) now.textContent = String(s[s.length - 1][1]);
          drawChart(canvas, s);
        }).catch(function () {});
      }
      tick();
      state.timers.push(setInterval(tick, 2000));
    });
  };

  function drawChart(canvas, samples) {
    var ctx = canvas.getContext('2d'), w = canvas.width, hgt = canvas.height;
    ctx.clearRect(0, 0, w, hgt);
    if (samples.length < 2) return;
    var vals = samples.map(function (s) { return s[1]; });
    var max = Math.max.apply(null, vals), min = Math.min.apply(null, vals);
    if (max === min) { max += 1; min -= 1; }
    ctx.strokeStyle = '#e2e4ea'; ctx.fillStyle = '#6b7080'; ctx.font = '12px sans-serif';
    for (var i = 0; i <= 4; i++) {
      var y = 10 + (hgt - 30) * i / 4;
      ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(w - 6, y); ctx.stroke();
      ctx.fillText((max - (max - min) * i / 4).toFixed(1), 2, y + 4);
    }
    ctx.strokeStyle = '#2d5bff'; ctx.lineWidth = 2; ctx.beginPath();
    samples.forEach(function (s, idx) {
      var x = 40 + (w - 46) * idx / (samples.length - 1);
      var y = 10 + (hgt - 30) * (1 - (s[1] - min) / (max - min));
      if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  /* ---- weekly menu */
  var MEAL_KEYS = ['breakfast', 'midmorning', 'lunch', 'snack', 'dinner'];
  function area(obj, path, label, meal) {
    var el = h('textarea', { rows: 2, maxlength: 300, autocomplete: 'off' });
    el.value = get(obj, path) || '';
    el.addEventListener('input', function () { set(obj, path, el.value); });
    return h('div', { class: 'mfield m-' + meal }, h('label', null, label), el);
  }
  function weekLabel(n, name) { return t('menu_week', { n: n }) + (name ? ' · ' + name : ''); }

  VIEWS.menu = function () {
    return api('GET', '/api/v1/admin/menu').then(function (r) {
      var menu = r.menu, sel = 0, box = h('div'), head = h('div'), body = h('div');
      function blankWeek() { return { name: '', days: [0, 1, 2, 3, 4, 5, 6].map(function () { return {}; }), shared: {} }; }
      function persist() {
        return api('PUT', '/api/v1/admin/menu', menu).then(function (x) { menu = x.menu; r = x; flash(box, 'ok', t('saved')); sel = Math.min(sel, Math.max(menu.weeks.length - 1, 0)); draw(); });
      }
      function drawHead() {
        clear(head);
        if (!r.configured) return;
        var nameOf = function (w) { return w.name ? ' · ' + w.name : ''; };
        var opts = menu.weeks.map(function (w, i) { return h('option', { value: String(i + 1), selected: i + 1 === r.current.number }, weekLabel(i + 1, w.name)); });
        var pick = h('select', null, opts);
        head.appendChild(h('div', { class: 'card' }, h('h3', null, t('menu_current')),
          h('div', { class: 'menu-now' },
            h('div', { class: 'big' }, h('b', null, String(r.current.number)), h('span', null, t('menu_now_is', { n: r.current.number, name: nameOf(r.current) }))),
            h('div', { class: 'muted' }, t('menu_next_is', { n: r.next.number, name: r.next.name ? ' · ' + r.next.name : '' }))),
          h('div', { class: 'row' }, h('div', null, h('label', null, t('menu_set_current')), pick),
            h('div', null, btn(t('menu_apply'), function () {
              return api('PUT', '/api/v1/admin/menu', menu).then(function () { return api('POST', '/api/v1/admin/menu/current-week', { week: Number(pick.value) }); })
                .then(function (x) { menu = x.menu; r = x; flash(box, 'ok', t('menu_applied')); draw(); });
            }, 'pri'))),
          h('p', { class: 'muted' }, t('menu_rotation'))));
      }
      function drawMeals() {
        var row = h('div', { class: 'row tight' });
        MEAL_KEYS.forEach(function (m) {
          var el = h('input', { type: 'checkbox', checked: menu.meals.indexOf(m) >= 0 });
          el.addEventListener('change', function () {
            menu.meals = MEAL_KEYS.filter(function (k) { return k === m ? el.checked : menu.meals.indexOf(k) >= 0; });
            drawWeek();
          });
          row.appendChild(h('label', { class: 'chk' }, el, t('meal_' + m)));
        });
        return h('div', { class: 'card' }, h('h3', null, t('menu_meals')), h('p', { class: 'muted' }, t('menu_meals_help')), row);
      }
      var weekBox = h('div');
      function drawWeek() {
        clear(weekBox);
        var w = menu.weeks[sel];
        if (!w) return;
        var tabs = h('div', { class: 'wtabs', role: 'tablist' });
        menu.weeks.forEach(function (x, i) {
          tabs.appendChild(h('button', { class: 'wtab' + (i === sel ? ' on' : ''), type: 'button', role: 'tab', 'aria-selected': i === sel ? 'true' : 'false', onclick: function () { sel = i; drawWeek(); } },
            String(i + 1), r.configured && r.current.number === i + 1 ? h('i', { title: t('menu_current') }) : null));
        });
        if (menu.weeks.length < 12) tabs.appendChild(h('button', { class: 'wtab add', type: 'button', 'aria-label': t('menu_add_week'), title: t('menu_add_week'), onclick: function () { menu.weeks.push(blankWeek()); sel = menu.weeks.length - 1; drawWeek(); } }, icon('plus')));
        function move(d) {
          var j = sel + d;
          if (j < 0 || j >= menu.weeks.length) return;
          var x = menu.weeks[sel]; menu.weeks[sel] = menu.weeks[j]; menu.weeks[j] = x; sel = j; drawWeek();
        }
        var days = h('div', { class: 'mdays' });
        t('days_long').split(',').forEach(function (dn, i) {
          var day = h('div', { class: 'mday' }, h('h4', null, dn));
          menu.meals.forEach(function (m) { day.appendChild(area(w, 'days.' + i + '.' + m, t('meal_' + m), m)); });
          days.appendChild(day);
        });
        var shared = h('div', { class: 'mshared' }, h('h4', null, t('menu_shared')), h('p', { class: 'muted' }, t('menu_shared_help')));
        var srow = h('div', { class: 'mdays wide' });
        menu.meals.forEach(function (m) { srow.appendChild(area(w, 'shared.' + m, t('meal_' + m), m)); });
        shared.appendChild(srow);
        weekBox.appendChild(h('div', { class: 'card' }, h('h3', null, t('menu_weeks')), tabs,
          h('div', { class: 'row' }, input(w, 'name', t('menu_week_name'))),
          menu.meals.length ? [days, shared] : null,
          h('div', { class: 'actions' },
            h('button', { class: 'btn', type: 'button', title: t('menu_move_left'), 'aria-label': t('menu_move_left'), disabled: sel === 0, onclick: function () { move(-1); } }, icon('up')),
            h('button', { class: 'btn', type: 'button', title: t('menu_move_right'), 'aria-label': t('menu_move_right'), disabled: sel === menu.weeks.length - 1, onclick: function () { move(1); } }, icon('down')),
            h('button', { class: 'btn', type: 'button', onclick: function () { if (menu.weeks.length >= 12) return; menu.weeks.splice(sel + 1, 0, JSON.parse(JSON.stringify(w))); sel += 1; drawWeek(); } }, icon('copy'), t('menu_dup_week')),
            h('button', { class: 'btn bad', type: 'button', onclick: function () { if (!confirm(t('menu_del_confirm'))) return; menu.weeks.splice(sel, 1); sel = Math.max(0, sel - 1); draw(); } }, t('menu_del_week')))));
      }
      function draw() {
        drawHead();
        clear(body);
        if (!menu.weeks.length) {
          body.appendChild(h('div', { class: 'empty' }, h('p', null, t('menu_none')), btn(t('menu_first'), function () { menu.weeks.push(blankWeek()); sel = 0; draw(); }, 'pri')));
          return;
        }
        body.appendChild(drawMeals());
        body.appendChild(weekBox);
        drawWeek();
        body.appendChild(h('div', { class: 'actions sticky-save' }, btn(t('save'), persist, 'pri')));
      }
      page(t('nav_menu'), [head, body]);
      draw();
    });
  };

  /* ---- agents (MCP) */
  function copyText(text, source) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    source.focus(); source.select();
    try { document.execCommand('copy'); } catch (e) { /* the text stays selected for a manual copy */ }
    return Promise.resolve();
  }
  function snippet(url, token) {
    return JSON.stringify({ mcpServers: { homehq: { url: url, headers: { Authorization: 'Bearer ' + token } } } }, null, 2);
  }

  VIEWS.spotify = function () {
    return Promise.all([loadConfig(), api('GET', '/api/v1/admin/spotify')]).then(function (rs) {
      var cfg = rs[0].config, st = rs[1], box = h('div'), flow = h('div'), speakers = h('div'), paste = { code: '' };
      page(t('nav_spotify'), box);
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('sp_steps_h')),
        h('ol', { class: 'steps' }, [1, 2, 3].map(function (n) { return h('li', null, t('sp_step' + n)); })),
        banner('ok', t('sp_limits'))));
      function listSpeakers() {
        return api('GET', '/api/v1/admin/spotify/devices').then(function (ds) {
          clear(speakers);
          if (!ds.length) { speakers.appendChild(h('p', { class: 'muted' }, t('sp_no_devices'))); return; }
          ds.forEach(function (d) { speakers.appendChild(h('div', null, h('span', { class: 'pill' + (d.active ? ' ok' : '') }, d.name), ' ', h('span', { class: 'muted' }, d.type))); });
        });
      }
      function draw() {
        var link = st.connected ? h('span', { class: 'pill ok' }, t('sp_connected')) : h('span', { class: 'pill warn' }, t('sp_notconnected'));
        clear(flow);
        flow.appendChild(h('h3', null, t('nav_spotify') + ' '), link);
        if (st.connected) {
          flow.appendChild(h('h3', null, t('sp_devices')));
          flow.appendChild(speakers);
          flow.appendChild(h('div', { class: 'row tight' }, btn(t('sp_check'), listSpeakers),
            btn(t('sp_disconnect'), function () { return api('DELETE', '/api/v1/admin/spotify').then(function () { st.connected = false; draw(); }); }, 'bad')));
          listSpeakers().catch(fail);
        }
      }
      var form = h('div', { class: 'card' },
        check(cfg, 'spotify.enabled', t('sp_enabled')),
        h('div', { class: 'row' }, input(cfg, 'spotify.client_id', t('sp_client'), { placeholder: '32 caracteres' }), input(cfg, 'spotify.redirect_uri', t('sp_redirect'))),
        h('div', { class: 'row tight' }, btn(t('save'), function () { return saveConfig(cfg, box); }, 'pri'),
          btn(t('sp_connect'), function () {
            return saveConfig(cfg, box).then(function () { return api('POST', '/api/v1/admin/spotify/authorize'); }).then(function (r) {
              var codeEl = h('input', { placeholder: 'http://127.0.0.1:8787/callback?code=…', autocomplete: 'off' });
              codeEl.addEventListener('input', function () { paste.code = codeEl.value; });
              clear(flow);
              flow.appendChild(h('p', null, h('a', { href: r.url, target: '_blank', rel: 'noopener noreferrer', class: 'btn' }, t('sp_open'))));
              flow.appendChild(h('div', null, h('label', null, t('sp_paste')), codeEl));
              flow.appendChild(h('div', { class: 'actions' }, btn(t('sp_finish'), function () {
                return api('POST', '/api/v1/admin/spotify/connect', { code: paste.code }).then(function () {
                  st.connected = true; draw(); flash(box, 'ok', t('sp_done'));
                });
              }, 'pri')));
            });
          })));
      box.appendChild(form);
      var card = h('div', { class: 'card' });
      card.appendChild(flow);
      box.appendChild(card);
      draw();
    });
  };

  VIEWS.agents = function () {
    return Promise.resolve().then(function () {
      var url = location.origin + '/mcp', box = h('div'), fresh = h('div');
      var form = { name: '', scope: 'read', expires_days: '90' };
      var urlEl = h('input', { readonly: true, value: url });
      var cfgEl = h('textarea', { readonly: true, class: 'snip', rows: 9 });
      cfgEl.value = snippet(url, 'hqa_…');
      var created = h('div', { class: 'card' }, h('h3', null, t('ag_new')),
        h('div', { class: 'row' }, input(form, 'name', t('ag_name')),
          select(form, 'scope', t('ag_scope'), [['read', t('ag_read')], ['full', t('ag_full')], ['trigger', t('ag_trigger')]]),
          select(form, 'expires_days', t('ag_exp'), [['30', t('ag_days', { n: 30 })], ['90', t('ag_days', { n: 90 })], ['365', t('ag_days', { n: 365 })], ['', t('never')]])),
        h('div', { class: 'actions' }, btn(t('ag_create'), function () {
          if (!form.name.trim()) throw new Error(t('name'));
          return api('POST', '/api/v1/admin/tokens', { name: form.name.trim(), scope: form.scope, expires_days: form.expires_days ? Number(form.expires_days) : null })
            .then(function (tk) {
              var tokEl = h('input', { readonly: true, value: tk.token, class: 'secret' });
              var cfg = h('textarea', { readonly: true, class: 'snip', rows: 9 });
              cfg.value = snippet(url, tk.token);
              clear(fresh);
              fresh.appendChild(h('div', { class: 'card fresh' }, h('h3', null, tk.name), banner('ok', t('ag_once')),
                h('label', null, t('ag_token')), tokEl,
                h('div', { class: 'actions' }, btn(t('ag_copy'), function () { return copyText(tk.token, tokEl).then(function () { flash(box, 'ok', t('ag_copied')); }); })),
                h('label', null, t('ag_config')), cfg,
                h('div', { class: 'actions' }, btn(t('ag_copy'), function () { return copyText(cfg.value, cfg).then(function () { flash(box, 'ok', t('ag_copied')); }); }))));
              form.name = '';
              return listTokens();
            });
        }, 'pri')));
      var listBox = h('div');
      function status(tk) {
        if (tk.revoked) return h('span', { class: 'pill bad' }, t('ag_revoked'));
        if (tk.expires_at && new Date(tk.expires_at.endsWith('Z') ? tk.expires_at : tk.expires_at + 'Z') < new Date()) return h('span', { class: 'pill warn' }, t('ag_expired'));
        return h('span', { class: 'pill ok' }, t('ag_active'));
      }
      function listTokens() {
        return api('GET', '/api/v1/admin/tokens').then(function (rows) {
          clear(listBox);
          if (!rows.length) { listBox.appendChild(h('p', { class: 'muted' }, t('ag_none'))); return; }
          var tb = h('table', null, h('tr', null, h('th', null, t('name')), h('th', null, t('ag_token')), h('th', null, t('ag_scope')), h('th', null, t('status')), h('th', null, t('ag_last')), h('th', null, t('ag_expires')), h('th', null, '')));
          rows.forEach(function (tk) {
            tb.appendChild(h('tr', null, h('td', null, tk.name), h('td', null, h('code', null, tk.prefix + '…')),
              h('td', null, h('span', { class: 'pill' }, tk.scope === 'full' ? t('ag_full') : tk.scope === 'trigger' ? t('ag_trigger') : t('ag_read'))), h('td', null, status(tk)),
              h('td', null, fmtDate(tk.last_used_at)), h('td', null, tk.expires_at ? fmtDate(tk.expires_at) : t('never')),
              h('td', null, tk.revoked ? null : btn(t('revoke'), function () {
                if (!confirm(t('ag_revoke_confirm'))) return;
                return api('DELETE', '/api/v1/admin/tokens/' + tk.id).then(listTokens);
              }, 'bad'))));
          });
          listBox.appendChild(tb);
        });
      }
      page(t('nav_agents'), box);
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('ag_url')), h('div', { class: 'copyrow' }, urlEl, btn(t('ag_copy'), function () { return copyText(url, urlEl).then(function () { flash(box, 'ok', t('ag_copied')); }); })),
        h('label', null, t('ag_config')), cfgEl, banner('err', t('ag_security'))));
      var haSnippet = [
        'rest_command:',
        '  homehq_camera:',
        '    url: "' + location.origin + '/api/v1/trigger"',
        '    method: POST',
        '    content_type: "application/json"',
        '    headers:',
        '      Authorization: "Bearer hqa_…"',
        '    payload: >-',
        '      {"action":"show_view","view":"cameras","camera":"{{ camera }}","device":"{{ device | default(\'\') }}","duration_s":{{ duration | default(30) }}}',
        '  homehq_aviso:',
        '    url: "' + location.origin + '/api/v1/trigger"',
        '    method: POST',
        '    content_type: "application/json"',
        '    headers:',
        '      Authorization: "Bearer hqa_…"',
        '    payload: >-',
        '      {"action":"alert","message":"{{ message }}","speak":true,"device":"{{ device | default(\'\') }}"}'
      ].join('\n');
      var haEl = h('textarea', { readonly: true, class: 'snip', rows: 18 });
      haEl.value = haSnippet;
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('ag_ha_h')), h('p', { class: 'muted' }, t('ag_ha_help')), haEl,
        h('div', { class: 'actions' }, btn(t('ag_copy'), function () { return copyText(haSnippet, haEl).then(function () { flash(box, 'ok', t('ag_copied')); }); })),
        h('p', { class: 'muted' }, t('ag_ha_use'))));
      box.appendChild(created);
      box.appendChild(fresh);
      box.appendChild(h('div', { class: 'card' }, h('h3', null, t('ag_tokens')), listBox));
      return listTokens();
    });
  };

  VIEWS.account = function () {
    page(t('nav_account'), [h('div', { class: 'card' }, h('h3', null, t('change_pw')), passwordForm())]);
    return Promise.resolve();
  };

  /* ------------------------------------------------------------------ start */
  document.documentElement.lang = lang;
  rawFetch('GET', '/api/v1/admin/auth/me').then(function (r) {
    if (r.ok) return r.json();
    return rawFetch('POST', '/api/v1/admin/auth/refresh').then(function (x) { return x.ok ? x.json() : null; });
  }).then(function (u) { if (u) { state.user = u; boot(); } else showLogin(); })
    .catch(function () { showLogin(); });
})();
