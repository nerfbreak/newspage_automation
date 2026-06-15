package com.newspage.optimize.data

import com.newspage.optimize.BuildConfig
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

enum class ServerState {
    CHECKING,      // Initial health check
    WAKING,        // Server is cold-starting
    ONLINE,        // Server is ready
    OFFLINE,       // Server is unreachable (non-cold-start)
}

/**
 * Manages server health state with cold-start detection.
 * Render free tier cold starts take ~30s; we show "Waking server..." during this period.
 */
object ServerStatusManager {
    private val _state = MutableStateFlow(ServerState.CHECKING)
    val state: StateFlow<ServerState> = _state

    private val _wakeElapsedMs = MutableStateFlow(0L)
    val wakeElapsedMs: StateFlow<Long> = _wakeElapsedMs

    suspend fun checkHealth() {
        _state.value = ServerState.CHECKING
        _wakeElapsedMs.value = 0L

        try {
            val resp = ApiService.api.healthCheck()
            if (resp.isSuccessful) {
                _state.value = ServerState.ONLINE
                return
            }
        } catch (_: Exception) {
            // First request failed - could be cold start
        }

        // Server might be cold-starting; poll with backoff
        _state.value = ServerState.WAKING
        val startTime = System.currentTimeMillis()
        val maxWait = 90_000L // 90 seconds max
        val pollInterval = 5_000L // Check every 5 seconds

        while (System.currentTimeMillis() - startTime < maxWait) {
            delay(pollInterval)
            _wakeElapsedMs.value = System.currentTimeMillis() - startTime

            try {
                val resp = ApiService.api.healthCheck()
                if (resp.isSuccessful) {
                    _state.value = ServerState.ONLINE
                    return
                }
            } catch (_: Exception) {
                // Keep polling
            }
        }

        _state.value = ServerState.OFFLINE
    }

    fun markOnline() {
        _state.value = ServerState.ONLINE
    }

    fun markOffline() {
        _state.value = ServerState.OFFLINE
    }
}
