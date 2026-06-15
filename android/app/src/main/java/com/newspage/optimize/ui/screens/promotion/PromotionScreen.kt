package com.newspage.optimize.ui.screens.promotion

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.newspage.optimize.ui.components.TerminalLogView
import com.newspage.optimize.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PromotionScreen(
    onBack: () -> Unit,
    viewModel: PromotionViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Promotion Comparison", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
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
            // Error
            if (state.error != null) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = BrandError.copy(alpha = 0.1f)),
                    modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                ) {
                    Text(state.error!!, color = BrandError, fontSize = 13.sp, modifier = Modifier.padding(12.dp))
                }
            }

            // ── SharePoint File Upload ──
            Text("SHAREPOINT DATA SOURCE", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
            Spacer(Modifier.height(8.dp))

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    val filePicker = rememberLauncherForActivityResult(
                        ActivityResultContracts.GetContent()
                    ) { uri: Uri? ->
                        uri?.let {
                            val name = uri.lastPathSegment?.substringAfterLast('/') ?: "tracker.xlsx"
                            viewModel.setSharepointFile(it, name)
                        }
                    }

                    Text(
                        "Upload Newspage BDP Tracker.xlsx",
                        fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.height(8.dp))

                    OutlinedButton(
                        onClick = { filePicker.launch("*/*") },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            if (state.sharepointName.isNotEmpty()) "\uD83D\uDCC4 ${state.sharepointName}"
                            else "Select Excel File (.xlsx)",
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }

            Spacer(Modifier.height(20.dp))

            // ── Extraction Settings ──
            Text("NEWSPAGE EXTRACTION SETTINGS", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
            Spacer(Modifier.height(8.dp))

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedTextField(
                            value = state.startDate,
                            onValueChange = viewModel::setStartDate,
                            label = { Text("Start Date") },
                            placeholder = { Text("DD/MM/YYYY", fontSize = 12.sp) },
                            modifier = Modifier.weight(1f),
                            textStyle = LocalTextStyle.current.copy(fontSize = 13.sp),
                        )
                        OutlinedTextField(
                            value = state.endDate,
                            onValueChange = viewModel::setEndDate,
                            label = { Text("End Date") },
                            placeholder = { Text("DD/MM/YYYY", fontSize = 12.sp) },
                            modifier = Modifier.weight(1f),
                            textStyle = LocalTextStyle.current.copy(fontSize = 13.sp),
                        )
                    }

                    Spacer(Modifier.height(16.dp))

                    Button(
                        onClick = { viewModel.startSync() },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        enabled = !state.syncing,
                        colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
                    ) {
                        if (state.syncing) {
                            CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Syncing & Extracting...", fontWeight = FontWeight.Bold)
                        } else if (state.syncDone) {
                            Text("Extraction Complete \u2713", fontWeight = FontWeight.Bold)
                        } else {
                            Text("Start Sync & Extraction", fontWeight = FontWeight.Bold)
                        }
                    }

                    if (state.syncDone && state.downloadRawUrl != null) {
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = { viewModel.downloadRawZip() }) {
                            Icon(Icons.Default.Download, "Download", Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("Download Raw Newspage ZIP", fontSize = 12.sp)
                        }
                    }
                }
            }

            Spacer(Modifier.height(20.dp))

            // ── Compare Section ──
            if (state.syncDone && state.sharepointUri != null) {
                Text("SMART COMPARISON ENGINE", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
                Spacer(Modifier.height(8.dp))

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Button(
                            onClick = { viewModel.startCompare() },
                            modifier = Modifier.fillMaxWidth().height(48.dp),
                            enabled = !state.comparing,
                            colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
                        ) {
                            if (state.comparing) {
                                CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                                Spacer(Modifier.width(8.dp))
                                Text("Analyzing...", fontWeight = FontWeight.Bold)
                            } else {
                                Text("Run Match Analysis", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                Spacer(Modifier.height(20.dp))
            }

            // ── Compare Results ──
            if (state.compareDone) {
                Text("COMPARISON RESULTS", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
                Spacer(Modifier.height(8.dp))

                // Metric cards
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = BrandSuccess.copy(alpha = 0.1f)),
                    ) {
                        Column(Modifier.padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Match", fontSize = 10.sp, color = BrandSuccess, fontWeight = FontWeight.SemiBold)
                            Text("${state.matchCount}", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = BrandSuccess)
                        }
                    }
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = BrandError.copy(alpha = 0.1f)),
                    ) {
                        Column(Modifier.padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Conflict", fontSize = 10.sp, color = BrandError, fontWeight = FontWeight.SemiBold)
                            Text("${state.conflictCount}", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = BrandError)
                        }
                    }
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFA500).copy(alpha = 0.1f)),
                    ) {
                        Column(Modifier.padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Missing", fontSize = 10.sp, color = Color(0xFFFFA500), fontWeight = FontWeight.SemiBold)
                            Text("${state.missingCount}", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color(0xFFFFA500))
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))

                // Filter chips
                Text("Filter Results", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val filters = listOf("All", "MATCH", "CONFLICT", "MISSING")
                    filters.forEach { f ->
                        FilterChip(
                            selected = state.filterStatus == f,
                            onClick = { viewModel.setFilter(f) },
                            label = { Text(f, fontSize = 11.sp) },
                        )
                    }
                }

                Spacer(Modifier.height(16.dp))

                // Download buttons
                Button(
                    onClick = { viewModel.downloadComparisonCsv() },
                    modifier = Modifier.fillMaxWidth().height(44.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = BrandSuccess),
                ) {
                    Icon(Icons.Default.Download, "Download", Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Download Comparison CSV", fontWeight = FontWeight.Bold)
                }

                Spacer(Modifier.height(8.dp))

                OutlinedButton(
                    onClick = { viewModel.downloadRawZip() },
                    modifier = Modifier.fillMaxWidth().height(44.dp),
                ) {
                    Icon(Icons.Default.Download, "Download", Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Download Raw Newspage ZIP", fontWeight = FontWeight.Bold)
                }

                if (state.savedMessage != null) {
                    Spacer(Modifier.height(8.dp))
                    Text(state.savedMessage!!, fontSize = 12.sp, color = BrandSuccess)
                }

                Spacer(Modifier.height(16.dp))
            }

            // ── Terminal Logs ──
            if (state.logs.isNotEmpty()) {
                Text("SYSTEM ACTIVITY LOG", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandTextMuted)
                Spacer(Modifier.height(8.dp))
                TerminalLogView(
                    messages = state.logs,
                    modifier = Modifier.heightIn(max = 400.dp),
                )
                Spacer(Modifier.height(16.dp))
            }

            Spacer(Modifier.height(60.dp))
        }
    }
}
