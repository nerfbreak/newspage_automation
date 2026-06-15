package com.newspage.optimize.ui.screens.sales

import android.app.Application
import android.content.ContentValues
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.newspage.optimize.data.ApiService
import com.newspage.optimize.data.WakeLockHelper
import com.newspage.optimize.data.WSMessage
import com.newspage.optimize.data.WebSocketManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import java.text.SimpleDateFormat
import java.util.*

data class SalesUiState(
    val distributors: List<String> = emptyList(),
    val selectedDistributor: String = "",
    val npUserId: String = "",
    val npPassword: String = "",
    val startDate: String = "",
    val endDate: String = "",
    val extracting: Boolean = false,
    val extractDone: Boolean = false,
    val jobId: String? = null,
    val downloadUrl: String? = null,
    val downloadFilename: String = "",
    val logs: List<WSMessage> = emptyList(),
    val error: String? = null,
    val savedMessage: String? = null,
)

class SalesViewModel(app: Application) : AndroidViewModel(app) {
    private val _state = MutableStateFlow(SalesUiState())
    val state: StateFlow<SalesUiState> = _state
    private var wsManager: WebSocketManager? = null

    init {
        initDates()
        loadDistributors()
    }

    private fun initDates() {
        val cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Jakarta"))
        val endStr = SimpleDateFormat("dd/MM/yyyy", Locale.US).format(cal.time)
        cal.set(Calendar.DAY_OF_MONTH, 1)
        val startStr = SimpleDateFormat("dd/MM/yyyy", Locale.US).format(cal.time)
        _state.value = _state.value.copy(startDate = startStr, endDate = endStr)
    }

    private fun loadDistributors() {
        viewModelScope.launch {
            try {
                val resp = ApiService.api.getDistributors()
                if (resp.isSuccessful) {
                    val list = resp.body()?.get("distributors") as? List<*> ?: emptyList<String>()
                    _state.value = _state.value.copy(distributors = list.mapNotNull { it as? String })
                }
            } catch (_: Exception) {}
        }
    }

    fun selectDistributor(name: String) {
        _state.value = _state.value.copy(selectedDistributor = name, error = null)
        viewModelScope.launch {
            try {
                val resp = ApiService.api.getCredentials(name)
                if (resp.isSuccessful) {
                    val userId = resp.body()?.get("np_user_id") as? String ?: ""
                    _state.value = _state.value.copy(npUserId = userId)
                }
            } catch (_: Exception) {}
        }
    }

    fun setPassword(v: String) { _state.value = _state.value.copy(npPassword = v) }
    fun setStartDate(v: String) { _state.value = _state.value.copy(startDate = v) }
    fun setEndDate(v: String) { _state.value = _state.value.copy(endDate = v) }

    fun startExtract() {
        val s = _state.value
        if (s.selectedDistributor.isBlank() || s.npPassword.isBlank()) {
            _state.value = s.copy(error = "Please fill in all fields")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(extracting = true, error = null, logs = emptyList(), extractDone = false)
            WakeLockHelper.acquire(getApplication(), "sales_extract")
            try {
                val resp = ApiService.api.extractSales(
                    distributor = s.selectedDistributor.toPlainBody(),
                    npUserId = s.npUserId.toPlainBody(),
                    npPassword = s.npPassword.toPlainBody(),
                    startDate = s.startDate.toPlainBody(),
                    endDate = s.endDate.toPlainBody(),
                )
                if (resp.isSuccessful) {
                    val jobId = resp.body()?.get("job_id") as String
                    _state.value = _state.value.copy(jobId = jobId)
                    connectWebSocket(jobId)
                } else {
                    val err = if (resp.code() == 409) "Another job is running" else "Extract failed (${resp.code()})"
                    _state.value = _state.value.copy(extracting = false, error = err)
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(extracting = false, error = e.message ?: "Connection failed")
            }
        }
    }

    private fun connectWebSocket(jobId: String) {
        wsManager?.disconnect()
        wsManager = WebSocketManager(jobId, onMessage = { msg -> handleWsMessage(msg) }, onClose = {})
        wsManager?.connect()
    }

    private fun handleWsMessage(msg: WSMessage) {
        when (msg.type) {
            "log" -> _state.value = _state.value.copy(logs = _state.value.logs + msg)
            "file_ready" -> {
                _state.value = _state.value.copy(
                    downloadUrl = msg.downloadUrl,
                    downloadFilename = msg.filename,
                )
            }
            "status" -> {
                if (msg.state == "completed") {
                    _state.value = _state.value.copy(extracting = false, extractDone = true)
                    WakeLockHelper.release()
                    wsManager?.disconnect()
                } else if (msg.state == "failed") {
                    _state.value = _state.value.copy(extracting = false, error = "Extraction failed")
                    WakeLockHelper.release()
                    wsManager?.disconnect()
                }
            }
        }
    }

    fun downloadFile() {
        val s = _state.value
        val jobId = s.jobId ?: return
        viewModelScope.launch {
            try {
                val resp = ApiService.api.downloadSales(jobId)
                if (resp.isSuccessful) {
                    val bytes = resp.body()?.bytes() ?: return@launch
                    saveFileToDownloads(s.downloadFilename.ifEmpty { "sales_data.csv" }, bytes, "text/csv")
                    _state.value = _state.value.copy(savedMessage = "File saved to Downloads")
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = "Download failed: ${e.message}")
            }
        }
    }

    private fun saveFileToDownloads(filename: String, bytes: ByteArray, mimeType: String) {
        val context = getApplication<Application>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, filename)
                put(MediaStore.Downloads.MIME_TYPE, mimeType)
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
            }
            val uri = context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            uri?.let {
                context.contentResolver.openOutputStream(it)?.use { out -> out.write(bytes) }
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        wsManager?.disconnect()
        WakeLockHelper.release()
    }

    private fun String.toPlainBody() = this.toRequestBody("text/plain".toMediaTypeOrNull())
}
