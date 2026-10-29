// Live state shared by every view. It starts empty and is filled by backend.js from the
// backend (or from the offline cache). Nothing in here is demo content.
window.DATA = {
  people: [],
  family: { id: 'family', name: 'Familia', color: '#111111', rgb: '17 17 17', ink: '#FFFFFF' },
  ALL: [],
  events: [],
  groceries: [],
  shopping: { provider: 'local', ok: true, stale: false, pending: 0 },
  ha: { enabled: false, connected: false, entities: [] },
  chores: { day: '', configured: 0, items: [] },
  cameras: [],
  music: { configured: false },
  menu: { configured: false, meals: [], weeks: [], start_week: 1, start_date: '' },
  weather: null,
  photos: [],
  presence: { ha_active: null },
  notices: []
};
