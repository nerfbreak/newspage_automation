package com.newspage.optimize.data

import android.util.Log
import com.newspage.optimize.BuildConfig
import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import org.json.JSONObject
import java.net.URI

data class WSMessage(
    val type: String = "",
    val module: String = "",
    val msg: String = "",
    val timestamp: String = "",
    val elapsedMs: Int = 0,
    val current: Int = 0,
    val total: Int = 0,
    val state: String = "",
    val downloadUrl: String = "",
    val filename: String = "",
)

/**
 * WebSocket client with automatic reconnection and log replay.
 * On reconnection, the server replays buffered logs for the job.
 * Max 5 reconnection attempts with exponential backoff.
 */
class WebSocketManager(
    private val jobId: String,
    private val onMessage: (WSMessage) -> Unit,
    private val onClose: () -> Unit = {},
    private val onReconnecting: (attempt: Int) -> Unit = {},
    private val onReconnectFailed: () -> Unit = {},
) {
    private var client: WebSocketClient? = null
    private var reconnectAttempt = 0
    private val maxReconnectAttempts = 5
    private var isManualClose = false
    private val logBuffer = mutableListOf<WSMessage>()

    /** All messages received so far (for replay on reconnect) */
    val messageHistory: List<WSMessage> get() = logBuffer.toList()

    fun connect() {
        isManualClose = false
        createAndConnect()
    }

    private fun createAndConnect() {
        val uri = URI("${BuildConfig.WS_BASE_URL}/ws/$jobId")
        client = object : WebSocketClient(uri) {
            override fun onOpen(handshake: ServerHandshake?) {
                Log.d("WS", "Connected to job $jobId (attempt $reconnectAttempt)")
                reconnectAttempt = 0 // Reset on successful connection
            }

            override fun onMessage(message: String?) {
                try {
                    val json = JSONObject(message ?: return)
                    val msg = WSMessage(
                        type = json.optString("type", ""),
                        module = json.optString("module", ""),
                        msg = json.optString("msg", ""),
                        timestamp = json.optString("timestamp", ""),
                        elapsedMs = json.optInt("elapsed_ms", 0),
                        current = json.optInt("current", 0),
                        total = json.optInt("total", 0),
                        state = json.optString("state", ""),
                        downloadUrl = json.optString("download_url", ""),
                        filename = json.optString("filename", ""),
                    )
                    // Buffer log messages for replay
                    if (msg.type == "log") {
                        logBuffer.add(msg)
                    }
                    onMessage(msg)
                } catch (e: Exception) {
                    Log.e("WS", "Parse error: $e")
                }
            }

            override fun onClose(code: Int, reason: String?, remote: Boolean) {
                Log.d("WS", "Disconnected: code=$code reason=$reason remote=$remote")
                if (!isManualClose && reconnectAttempt < maxReconnectAttempts) {
                    attemptReconnect()
                } else if (reconnectAttempt >= maxReconnectAttempts) {
                    Log.e("WS", "Max reconnection attempts reached")
                    onReconnectFailed()
                    onClose()
                } else {
                    onClose()
                }
            }

            override fun onError(ex: Exception?) {
                Log.e("WS", "Error: ${ex?.message}")
            }
        }
        client?.connect()
    }

    private fun attemptReconnect() {
        reconnectAttempt++
        onReconnecting(reconnectAttempt)

        // Exponential backoff: 2s, 4s, 8s, 16s, 32s
        val delayMs = (2000L * (1L shl (reconnectAttempt - 1))).coerceAtMost(30_000L)
        Log.d("WS", "Reconnecting in ${delayMs}ms (attempt $reconnectAttempt/$maxReconnectAttempts)")

        Thread {
            Thread.sleep(delayMs)
            if (!isManualClose) {
                createAndConnect()
            }
        }.start()
    }

    fun disconnect() {
        isManualClose = true
        client?.close()
        client = null
    }

    /** Clear the message buffer (call when navigating away from the screen) */
    fun clearBuffer() {
        logBuffer.clear()
    }
}
