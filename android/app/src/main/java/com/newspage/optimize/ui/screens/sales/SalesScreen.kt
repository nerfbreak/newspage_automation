package com.newspage.optimize.ui.screens.sales

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material3.*
import androidx.compose.runtime.*
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
fun SalesScreen(
    onBack: () -> Unit,
    viewModel: SalesViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sales Extraction", fontWeight = FontWeight.Bold) },
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

            // Setup card
            Text("SALES EXTRACTION SETUP", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
            Spacer(Modifier.height(8.dp))

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    // Distributor dropdown
                    var expanded by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = !expanded }) {
                        OutlinedTextField(
                            value = state.selectedDistributor,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Distributor") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                            modifier = Modifier.fillMaxWidth().menuAnchor(),
                        )
                        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                            state.distributors.forEach { name ->
                                DropdownMenuItem(
                                    text = { Text(name) },
                                    onClick = { viewModel.selectDistributor(name); expanded = false },
                                )
                            }
                        }
                    }

                    Spacer(Modifier.height(12.dp))

                    // NP User ID (read-only)
                    OutlinedTextField(
                        value = state.npUserId,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("NP User ID") },
                        modifier = Modifier.fillMaxWidth(),
                    )

                    Spacer(Modifier.height(12.dp))

                    // NP Password
                    OutlinedTextField(
                        value = state.npPassword,
                        onValueChange = viewModel::setPassword,
                        label = { Text("NP Password") },
                        modifier = Modifier.fillMaxWidth(),
                    )

                    Spacer(Modifier.height(12.dp))

                    // Date inputs
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

                    // Extract button
                    Button(
                        onClick = { viewModel.startExtract() },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        enabled = !state.extracting,
                        colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
                    ) {
                        if (state.extracting) {
                            CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Extracting Invoice Data...", fontWeight = FontWeight.Bold)
                        } else {
                            Text("Extract Invoice Details", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            Spacer(Modifier.height(20.dp))

            // Download section
            if (state.extractDone && state.downloadUrl != null) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = BrandSuccess.copy(alpha = 0.1f)),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(
                            "Extraction Complete!",
                            fontSize = 14.sp, fontWeight = FontWeight.Bold, color = BrandSuccess,
                        )
                        if (state.downloadFilename.isNotEmpty()) {
                            Text(state.downloadFilename, fontSize = 12.sp, color = BrandTextMuted)
                        }
                        Spacer(Modifier.height(12.dp))
                        Button(
                            onClick = { viewModel.downloadFile() },
                            modifier = Modifier.fillMaxWidth().height(44.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = BrandSuccess),
                        ) {
                            Icon(Icons.Default.Download, "Download", Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("Download Sales CSV", fontWeight = FontWeight.Bold)
                        }
                        if (state.savedMessage != null) {
                            Spacer(Modifier.height(8.dp))
                            Text(state.savedMessage!!, fontSize = 12.sp, color = BrandSuccess)
                        }
                    }
                }
                Spacer(Modifier.height(20.dp))
            }

            // Terminal logs
            if (state.logs.isNotEmpty()) {
                Text("SYSTEM ACTIVITY LOG", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandTextMuted)
                Spacer(Modifier.height(8.dp))
                TerminalLogView(
                    messages = state.logs,
                    modifier = Modifier.heightIn(max = 500.dp),
                )
                Spacer(Modifier.height(16.dp))
            }

            Spacer(Modifier.height(60.dp))
        }
    }
}
