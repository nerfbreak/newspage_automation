package com.newspage.optimize.ui.screens.login

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.newspage.optimize.data.ApiService
import com.newspage.optimize.data.ServerState
import com.newspage.optimize.data.ServerStatusManager
import com.newspage.optimize.data.TokenManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val username: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
    val isLoggedIn: Boolean = false,
    val lockRemaining: Int = 0,
    val serverState: ServerState = ServerState.CHECKING,
    val wakeElapsedMs: Long = 0L,
)

class LoginViewModel(app: Application) : AndroidViewModel(app) {
    private val tokenManager = TokenManager(app)
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState

    init {
        ApiService.init(tokenManager)
        checkServerHealth()
    }

    private fun checkServerHealth() {
        viewModelScope.launch {
            ServerStatusManager.checkHealth()
            // Keep UI state in sync with server state
            viewModelScope.launch {
                ServerStatusManager.state.collect { s ->
                    _uiState.value = _uiState.value.copy(serverState = s)
                }
            }
            viewModelScope.launch {
                ServerStatusManager.wakeElapsedMs.collect { ms ->
                    _uiState.value = _uiState.value.copy(wakeElapsedMs = ms)
                }
            }
        }
    }

    fun onUsernameChange(v: String) {
        _uiState.value = _uiState.value.copy(username = v, error = null)
    }

    fun onPasswordChange(v: String) {
        _uiState.value = _uiState.value.copy(password = v, error = null)
    }

    fun login() {
        val state = _uiState.value
        if (state.username.isBlank() || state.password.isBlank()) {
            _uiState.value = state.copy(error = "Please fill in all fields")
            return
        }

        viewModelScope.launch {
            _uiState.value = state.copy(isLoading = true, error = null)
            try {
                val response = ApiService.api.login(
                    mapOf("username" to state.username, "password" to state.password)
                )
                if (response.isSuccessful) {
                    val body = response.body()!!
                    val ok = body["ok"] as? Boolean ?: false
                    if (ok) {
                        val accessToken = body["access_token"] as String
                        val refreshToken = body["refresh_token"] as String
                        tokenManager.saveTokens(accessToken, refreshToken, state.username)
                        _uiState.value = _uiState.value.copy(isLoading = false, isLoggedIn = true)
                    } else {
                        val locked = body["locked"] as? Boolean ?: false
                        val remaining = (body["remaining"] as? Number)?.toInt() ?: 0
                        val attemptsLeft = (body["attempts_left"] as? Number)?.toInt() ?: 0
                        val errorMsg = body["error"] as? String ?: "Login failed"
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = errorMsg,
                            lockRemaining = if (locked) remaining else 0,
                        )
                        if (locked && remaining > 0) startLockoutTimer(remaining)
                    }
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Server error (${response.code()})",
                    )
                }
            } catch (e: Exception) {
                val msg = if (e.message?.contains("timeout") == true || e.message?.contains("Timeout") == true) {
                    "Server is waking up... Please try again."
                } else {
                    e.message ?: "Connection failed"
                }
                _uiState.value = _uiState.value.copy(isLoading = false, error = msg)
            }
        }
    }

    private fun startLockoutTimer(seconds: Int) {
        viewModelScope.launch {
            for (i in seconds downTo 1) {
                kotlinx.coroutines.delay(1000)
                _uiState.value = _uiState.value.copy(lockRemaining = i)
            }
            _uiState.value = _uiState.value.copy(lockRemaining = 0, error = null)
        }
    }
}
