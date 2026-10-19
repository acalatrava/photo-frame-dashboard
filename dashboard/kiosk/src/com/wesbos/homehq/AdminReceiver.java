package com.wesbos.homehq;

import android.app.admin.DeviceAdminReceiver;

/**
 * Only used to be allowed to call DevicePolicyManager.lockNow() so the frame can really turn its screen off.
 * Activate once with: adb shell dpm set-active-admin com.wesbos.homehq/.AdminReceiver
 */
public class AdminReceiver extends DeviceAdminReceiver { }
