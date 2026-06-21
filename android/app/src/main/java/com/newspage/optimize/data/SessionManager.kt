package com.newspage.optimize.data

import android.app.Application
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Monitors user activity and triggers auto-logout after [timeoutMs] of inactivity.
 * Attach to the app's main lifecycle in MainActivity.
 *
 * Usage:
 *   val sessionManager = SessionManager(application, onSessionExpired = { navigateToLogin() })
 *   ProcessLifecycleOwner.get().lifecycle.addObserver(sessionManager)
 *   // Call sessionManager.onUserInteraction() on each user touch event
 */
class SessionManager(
    private val app: Application,
    private val timeoutMs: Long = 3_600_000L, // 1 hour
    private val onSessionExpired: () -> Unit,
) : DefaultLifecycleObserver {

    private val _isExpired = MutableStateFlow(false)
    val isExpired: StateFlow<Boolean> = _isExpired

    private var lastActivityTime = System.currentTimeMillis()
    private var checkJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    override fun onStart(owner: LifecycleOwner) {
        // App comes to foreground — start checking
        startTimer()
    }

    override fun onStop(owner: LifecycleOwner) {
        // App goes to background — stop checking (preserve last activity time)
        stopTimer()
    }

    /** Call this on every user interaction (touch, scroll, etc.) */
    fun onUserInteraction() {
        lastActivityTime = System.currentTimeMillis()
    }

    private fun startTimer() {
        checkJob?.cancel()
        checkJob = scope.launch {
            while (isActive) {
                delay(60_000L) // Check every minute
                val elapsed = System.currentTimeMillis() - lastActivityTime
                if (elapsed >= timeoutMs) {
                    _isExpired.value = true
                    // Clear tokens
                    val tokenManager = TokenManager(app)
                    tokenManager.clear()
                    onSessionExpired()
                    break
                }
            }
        }
    }

    private fun stopTimer() {
        checkJob?.cancel()
        checkJob = null
    }

    fun reset() {
        lastActivityTime = System.currentTimeMillis()
        _isExpired.value = false
    }

    fun destroy() {
        stopTimer()
        scope.cancel()
    }
}
