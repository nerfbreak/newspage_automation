package com.newspage.optimize.ui.screens.dashboard

import android.app.Application
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.newspage.optimize.data.ApiService
import com.newspage.optimize.data.TokenManager
import com.newspage.optimize.ui.components.MetricCard
import com.newspage.optimize.ui.components.StatusPill
import com.newspage.optimize.ui.theme.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

// ViewModel
class DashboardViewModel(app: Application) : AndroidViewModel(app) {
    private val tokenManager = TokenManager(app)
    data class State(
        val username: String = "",
        val totalExtractions: Int = 0,
        val lastDist: String = "N/A",
        val totalDistributors: Int = 0,
        val dbConnected: Boolean = false,
        val loading: Boolean = true,
    )
    private val _state = MutableStateFlow(State())
    val state: StateFlow<State> = _state

    init {
        viewModelScope.launch {
            _state.value = _state.value.copy(username = tokenManager.getUsername() ?: "")
            loadDashboard()
        }
    }

    fun refresh() { viewModelScope.launch { loadDashboard() } }

    private suspend fun loadDashboard() {
        _state.value = _state.value.copy(loading = true)
        try {
            val resp = ApiService.api.getDashboard()
            if (resp.isSuccessful) {
                val body = resp.body()!!
                val metrics = body["metrics"] as? Map<*, *> ?: emptyMap<String, Any>()
                _state.value = State(
                    username = _state.value.username,
                    totalExtractions = (metrics["total_extractions"] as? Number)?.toInt() ?: 0,
                    lastDist = metrics["last_extracted_dist"] as? String ?: "N/A",
                    totalDistributors = (metrics["total_distributors"] as? Number)?.toInt() ?: 0,
                    dbConnected = metrics["db_connected"] as? Boolean ?: false,
                    loading = false,
                )
            }
        } catch (e: Exception) {
            _state.value = _state.value.copy(loading = false)
        }
    }

    suspend fun logout() { tokenManager.clear() }
}

// Screen
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    onNavigateToInventory: () -> Unit,
    onNavigateToSales: () -> Unit,
    onNavigateToPromotion: () -> Unit,
    onLogout: () -> Unit,
    viewModel: DashboardViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsState()
    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Automation Tool", fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = {
                        scope.launch { viewModel.logout(); onLogout() }
                    }) {
                        Icon(Icons.Default.Logout, "Logout")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            // Active session label
            Row {
                Text("ACTIVE SESSION  ", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
                Text(state.username.uppercase(), fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.height(16.dp))

            // Metric cards row
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Total Extractions", "${state.totalExtractions}", Modifier.weight(1f))
                MetricCard("Last Extraction", state.lastDist, Modifier.weight(1f), accent = true)
                MetricCard("Distributors", "${state.totalDistributors}", Modifier.weight(1f))
            }

            Spacer(Modifier.height(24.dp))

            // Navigation cards
            Text("Navigation", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 12.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                NavCard("Inventory Adjustment", "Sync real-time stock levels", Modifier.weight(1f), onNavigateToInventory)
                NavCard("Sales Extraction", "Extract distributor invoices", Modifier.weight(1f), onNavigateToSales)
                NavCard("Promotion Comparison", "Compare distributor pricing", Modifier.weight(1f), onNavigateToPromotion)
            }

            Spacer(Modifier.height(24.dp))

            // System health
            Text("System Health", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 12.dp))

            val dbColor = if (state.dbConnected) BrandSuccess else BrandError
            StatusPill("Database", if (state.dbConnected) "CONNECTED" else "DISCONNECTED", dbColor)

            Spacer(Modifier.height(12.dp))
            StatusPill("Playwright Bots", "STANDBY", BrandTextMuted)

            Spacer(Modifier.height(80.dp))

            Text(
                "\u00A9 2026 IT Support Newspage.",
                fontSize = 9.sp, color = BrandBlue.copy(alpha = 0.6f),
                modifier = Modifier.padding(bottom = 16.dp),
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NavCard(title: String, desc: String, modifier: Modifier, onClick: () -> Unit) {
    Card(
        modifier = modifier,
        onClick = onClick,
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(title, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Text(desc, fontSize = 12.sp, color = BrandTextMuted, lineHeight = 18.sp)
            Spacer(Modifier.height(16.dp))
            Text("Open \u2192", fontSize = 12.sp, color = BrandBlue, fontWeight = FontWeight.SemiBold)
        }
    }
}
