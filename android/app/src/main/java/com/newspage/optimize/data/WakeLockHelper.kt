package com.newspage.optimize.data

import android.annotation.SuppressLint
import android.content.Context
import android.os.PowerManager
import android.util.Log

/**
 * Manages a partial wake lock to keep the CPU running during long Playwright operations.
 * Playwright jobs can take 4-5 minutes; without a wake lock, Android may suspend the CPU.
 *
 * Usage:
 *   WakeLockHelper.acquire(context, "inventory_extract")
 *   try { ... do work ... }
 *   finally { WakeLockHelper.release() }
 */
object WakeLockHelper {
    private var wakeLock: PowerManager.WakeLock? = null
    private const val TAG = "OptimizeWakeLock"

    @SuppressLint("WakelockTimeout")
    fun acquire(context: Context, tag: String) {
        release() // Release any existing lock
        val pm = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "OptimizeNP::$tag",
        ).apply {
            setReferenceCounted(false)
            acquire(10 * 60 * 1000L) // 10-minute safety timeout
        }
        Log.d(TAG, "Wake lock acquired for: $tag")
    }

    fun release() {
        wakeLock?.let {
            if (it.isHeld) {
                it.release()
                Log.d(TAG, "Wake lock released")
            }
        }
        wakeLock = null
    }

    val isHeld: Boolean get() = wakeLock?.isHeld == true
}
