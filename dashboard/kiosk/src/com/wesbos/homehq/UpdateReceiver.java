package com.wesbos.homehq;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Android kills the app while it replaces itself; this brings the new version straight back to the screen. */
public class UpdateReceiver extends BroadcastReceiver {
  @Override public void onReceive(Context context, Intent intent) {
    if (!Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())) return;
    context.startActivity(new Intent(context, MainActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP));
  }
}
