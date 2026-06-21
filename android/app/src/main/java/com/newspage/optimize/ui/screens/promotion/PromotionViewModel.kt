package com.newspage.optimize.ui.screens.promotion

import android.app.Application
import android.content.ContentValues
import android.net.Uri
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
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.text.SimpleDateFormat
import java.util.*

data class PromotionUiState(
    val startDate: String = "",
    val endDate: String = "",
    val sharepointUri: Uri? = null,
    val sharepointName: String = "",
    // Sync
    val syncing: Boolean = false,
    val syncDone: Boolean = false,
    val syncJobId: String? = null,
    // Compare
    val comparing: Boolean = false,
    val compareDone: Boolean = false,
    val matchCount: Int = 0,
    val conflictCount: Int = 0,
    val missingCount: Int = 0,
    val filterStatus: String = "All",
    val csvData: String? = null,
    // Downloads
    val downloadRawUrl: String? = null,
    val downloadFilename: String = "",
    val savedMessage: String? = null,
    // Logs
    val logs: List<WSMessage> = emptyList(),
    val error: String? = null,
)

class PromotionViewModel(app: Application) : AndroidViewModel(app) {
    private val _state = MutableStateFlow(PromotionUiState())
    val state: StateFlow<PromotionUiState> = _state
    private var wsManager: WebSocketManager? = null

    init {
        initDates()
    }

    private fun initDates() {
        val cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Jakarta"))
        val endStr = SimpleDateFormat("dd/MM/yyyy", Locale.US).format(cal.time)
        cal.set(Calendar.DAY_OF_MONTH, 1)
        val startStr = SimpleDateFormat("dd/MM/yyyy", Locale.US).format(cal.time)
        _state.value = _state.value.copy(startDate = startStr, endDate = endStr)
    }

    fun setStartDate(v: String) { _state.value = _state.value.copy(startDate = v) }
    fun setEndDate(v: String) { _state.value = _state.value.copy(endDate = v) }
    fun setSharepointFile(uri: Uri, name: String) { _state.value = _state.value.copy(sharepointUri = uri, sharepointName = name) }
    fun setFilter(v: String) { _state.value = _state.value.copy(filterStatus = v) }

    fun startSync() {
        val s = _state.value
        if (s.startDate.isBlank() || s.endDate.isBlank()) {
            _state.value = s.copy(error = "Please set date range")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(syncing = true, error = null, logs = emptyList(), syncDone = false)
            WakeLockHelper.acquire(getApplication(), "promotion_sync")
            try {
                val resp = ApiService.api.syncPromotion(
                    startDate = s.startDate.toPlainBody(),
                    endDate = s.endDate.toPlainBody(),
                )
                if (resp.isSuccessful) {
                    val jobId = resp.body()?.get("job_id") as String
                    _state.value = _state.value.copy(syncJobId = jobId)
                    connectWebSocket(jobId)
                } else {
                    val err = if (resp.code() == 409) "Another job is running" else "Sync failed (${resp.code()})"
                    _state.value = _state.value.copy(syncing = false, error = err)
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(syncing = false, error = e.message ?: "Connection failed")
            }
        }
    }

    fun startCompare() {
        val s = _state.value
        if (s.syncJobId == null || s.sharepointUri == null) {
            _state.value = s.copy(error = "Sync data and SharePoint file required")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(comparing = true, error = null)
            try {
                val context = getApplication<Application>()
                val inputStream = context.contentResolver.openInputStream(s.sharepointUri!!)
                val bytes = inputStream?.readBytes() ?: ByteArray(0)
                inputStream?.close()

                val mimeType = context.contentResolver.getType(s.sharepointUri!!) ?: "application/octet-stream"
                val requestBody = bytes.toRequestBody(mimeType.toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("sharepoint_file", s.sharepointName, requestBody)

                val resp = ApiService.api.comparePromotion(
                    jobId = s.syncJobId!!.toPlainBody(),
                    sharepointFile = filePart,
                    filterStatus = s.filterStatus.toPlainBody(),
                )
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    _state.value = _state.value.copy(
                        comparing = false, compareDone = true,
                        matchCount = (body["match_count"] as? Number)?.toInt() ?: 0,
                        conflictCount = (body["conflict_count"] as? Number)?.toInt() ?: 0,
                        missingCount = (body["missing_count"] as? Number)?.toInt() ?: 0,
                        csvData = body["csv_data"] as? String,
                    )
                } else {
                    _state.value = _state.value.copy(comparing = false, error = "Compare failed (${resp.code()})")
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(comparing = false, error = e.message ?: "Compare failed")
            }
        }
    }

    fun downloadComparisonCsv() {
        val s = _state.value
        val csvData = s.csvData ?: return
        val now = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        saveFileToDownloads("promo_comparison_$now.csv", csvData.toByteArray(), "text/csv")
        _state.value = _state.value.copy(savedMessage = "Comparison CSV saved")
    }

    fun downloadRawZip() {
        val jobId = _state.value.syncJobId ?: return
        viewModelScope.launch {
            try {
                val resp = ApiService.api.downloadPromotion(jobId)
                if (resp.isSuccessful) {
                    val bytes = resp.body()?.bytes() ?: return@launch
                    saveFileToDownloads("newspage_promo_extraction.zip", bytes, "application/zip")
                    _state.value = _state.value.copy(savedMessage = "Raw ZIP saved to Downloads")
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = "Download failed: ${e.message}")
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
                    downloadRawUrl = msg.downloadUrl,
                    downloadFilename = msg.filename,
                )
            }
            "status" -> {
                if (msg.state == "completed") {
                    _state.value = _state.value.copy(syncing = false, syncDone = true)
                    WakeLockHelper.release()
                    wsManager?.disconnect()
                } else if (msg.state == "failed") {
                    _state.value = _state.value.copy(syncing = false, error = "Sync failed")
                    WakeLockHelper.release()
                    wsManager?.disconnect()
                }
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
