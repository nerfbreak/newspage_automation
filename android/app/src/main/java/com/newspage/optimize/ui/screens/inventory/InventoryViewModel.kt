package com.newspage.optimize.ui.screens.inventory

import android.app.Application
import android.net.Uri
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

data class InventoryUiState(
    val distributors: List<String> = emptyList(),
    val selectedDistributor: String = "",
    val npUserId: String = "",
    val npPassword: String = "",
    // Step 1: Extract
    val extractJobId: String? = null,
    val extracting: Boolean = false,
    val extractDone: Boolean = false,
    val extractItemCount: Int = 0,
    // Step 2: Compare
    val distFileUri: Uri? = null,
    val distFileName: String = "",
    val comparing: Boolean = false,
    val compareDone: Boolean = false,
    val matchCount: Int = 0,
    val mismatchCount: Int = 0,
    val mismatchRows: List<Map<String, Any>> = emptyList(),
    // Column mapping
    val skuColNp: String = "Product Code",
    val descColNp: String = "Product Description",
    val qtyColNp: String = "Stock Available",
    val skuColDist: String = "",
    val qtyColDist: String = "",
    // Step 3: Execute
    val executing: Boolean = false,
    val executeDone: Boolean = false,
    val executeJobId: String? = null,
    // Logs
    val logs: List<WSMessage> = emptyList(),
    val progress: Float = 0f,
    val progressCurrent: Int = 0,
    val progressTotal: Int = 0,
    // General
    val error: String? = null,
    val loading: Boolean = false,
)

class InventoryViewModel(app: Application) : AndroidViewModel(app) {
    private val _state = MutableStateFlow(InventoryUiState())
    val state: StateFlow<InventoryUiState> = _state
    private var wsManager: WebSocketManager? = null

    init {
        loadDistributors()
    }

    private fun loadDistributors() {
        viewModelScope.launch {
            try {
                val resp = ApiService.api.getDistributors()
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    val list = body["distributors"] as? List<*> ?: emptyList<String>()
                    val names = list.mapNotNull { it as? String }
                    _state.value = _state.value.copy(distributors = names, loading = false)
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = "Failed to load distributors", loading = false)
            }
        }
    }

    fun selectDistributor(name: String) {
        _state.value = _state.value.copy(selectedDistributor = name, error = null)
        // Fetch credentials for this distributor
        viewModelScope.launch {
            try {
                val resp = ApiService.api.getCredentials(name)
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    val userId = body["np_user_id"] as? String ?: ""
                    _state.value = _state.value.copy(npUserId = userId)
                }
            } catch (_: Exception) {}
        }
    }

    fun setPassword(v: String) { _state.value = _state.value.copy(npPassword = v) }
    fun setDistFileUri(uri: Uri, name: String) { _state.value = _state.value.copy(distFileUri = uri, distFileName = name) }
    fun setSkuColNp(v: String) { _state.value = _state.value.copy(skuColNp = v) }
    fun setDescColNp(v: String) { _state.value = _state.value.copy(descColNp = v) }
    fun setQtyColNp(v: String) { _state.value = _state.value.copy(qtyColNp = v) }
    fun setSkuColDist(v: String) { _state.value = _state.value.copy(skuColDist = v) }
    fun setQtyColDist(v: String) { _state.value = _state.value.copy(qtyColDist = v) }

    // Step 1: Extract
    fun startExtract() {
        val s = _state.value
        if (s.selectedDistributor.isBlank() || s.npUserId.isBlank() || s.npPassword.isBlank()) {
            _state.value = s.copy(error = "Please fill in all fields")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(extracting = true, error = null, logs = emptyList())
            WakeLockHelper.acquire(getApplication(), "inventory_extract")
            try {
                val dist = s.selectedDistributor.toPlainBody()
                val user = s.npUserId.toPlainBody()
                val pass = s.npPassword.toPlainBody()
                val resp = ApiService.api.extractInventory(dist, user, pass)
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    val jobId = body["job_id"] as String
                    _state.value = _state.value.copy(extractJobId = jobId)
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

    // Step 2: Compare
    fun startCompare() {
        val s = _state.value
        if (s.extractJobId == null || s.distFileUri == null) {
            _state.value = s.copy(error = "Extract data and distributor file required")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(comparing = true, error = null)
            try {
                val context = getApplication<Application>()
                val inputStream = context.contentResolver.openInputStream(s.distFileUri!!)
                val bytes = inputStream?.readBytes() ?: ByteArray(0)
                inputStream?.close()

                val mimeType = context.contentResolver.getType(s.distFileUri!!) ?: "application/octet-stream"
                val requestBody = bytes.toRequestBody(mimeType.toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("dist_file", s.distFileName, requestBody)

                val resp = ApiService.api.compareInventory(
                    jobId = s.extractJobId!!.toPlainBody(),
                    distFile = filePart,
                    skuColNp = s.skuColNp.toPlainBody(),
                    descColNp = s.descColNp.toPlainBody(),
                    qtyColNp = s.qtyColNp.toPlainBody(),
                    skuColDist = s.skuColDist.toPlainBody(),
                    qtyColDist = s.qtyColDist.toPlainBody(),
                )
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    val matchCount = (body["total_match"] as? Number)?.toInt() ?: 0
                    val mismatchCount = (body["total_mismatch"] as? Number)?.toInt() ?: 0
                    val rows = body["rows"] as? List<Map<String, Any>> ?: emptyList()
                    _state.value = _state.value.copy(
                        comparing = false, compareDone = true,
                        matchCount = matchCount, mismatchCount = mismatchCount, mismatchRows = rows,
                    )
                } else {
                    _state.value = _state.value.copy(comparing = false, error = "Compare failed (${resp.code()})")
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(comparing = false, error = e.message ?: "Compare failed")
            }
        }
    }

    // Step 3: Execute
    fun startExecute() {
        val s = _state.value
        if (s.extractJobId == null || s.npUserId.isBlank() || s.npPassword.isBlank()) {
            _state.value = s.copy(error = "Credentials required for execution")
            return
        }
        viewModelScope.launch {
            _state.value = s.copy(executing = true, error = null, logs = emptyList())
            WakeLockHelper.acquire(getApplication(), "inventory_execute")
            try {
                val resp = ApiService.api.executeAdjustment(
                    jobId = s.extractJobId!!.toPlainBody(),
                    npUserId = s.npUserId.toPlainBody(),
                    npPassword = s.npPassword.toPlainBody(),
                )
                if (resp.isSuccessful) {
                    val body = resp.body()!!
                    val jobId = body["job_id"] as String
                    _state.value = _state.value.copy(executeJobId = jobId)
                    connectWebSocket(jobId)
                } else {
                    val err = if (resp.code() == 409) "Another job is running" else "Execute failed (${resp.code()})"
                    _state.value = _state.value.copy(executing = false, error = err)
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(executing = false, error = e.message ?: "Connection failed")
            }
        }
    }

    private fun connectWebSocket(jobId: String) {
        wsManager?.disconnect()
        wsManager = WebSocketManager(jobId, onMessage = { msg -> handleWsMessage(msg) }, onClose = { })
        wsManager?.connect()
    }

    private fun handleWsMessage(msg: WSMessage) {
        when (msg.type) {
            "log" -> {
                _state.value = _state.value.copy(logs = _state.value.logs + msg)
            }
            "progress" -> {
                val pct = if (msg.total > 0) msg.current.toFloat() / msg.total else 0f
                _state.value = _state.value.copy(progress = pct, progressCurrent = msg.current, progressTotal = msg.total)
            }
            "status" -> {
                when (msg.state) {
                    "completed" -> {
                        val s = _state.value
                        when {
                            s.extracting -> _state.value = s.copy(extracting = false, extractDone = true, extractItemCount = 0)
                            s.executing -> _state.value = s.copy(executing = false, executeDone = true)
                        }
                        WakeLockHelper.release()
                        wsManager?.disconnect()
                    }
                    "failed" -> {
                        val s = _state.value
                        when {
                            s.extracting -> _state.value = s.copy(extracting = false, error = "Extraction failed")
                            s.executing -> _state.value = s.copy(executing = false, error = "Execution failed")
                        }
                        WakeLockHelper.release()
                        wsManager?.disconnect()
                    }
                }
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
