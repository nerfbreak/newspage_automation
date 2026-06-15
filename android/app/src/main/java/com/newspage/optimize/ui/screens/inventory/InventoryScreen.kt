package com.newspage.optimize.ui.screens.inventory

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
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
fun InventoryScreen(
    onBack: () -> Unit,
    viewModel: InventoryViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Inventory Adjustment", fontWeight = FontWeight.Bold) },
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
                    Text(
                        state.error!!, color = BrandError, fontSize = 13.sp,
                        modifier = Modifier.padding(12.dp),
                    )
                }
            }

            // ── Step 1: Newspage Stock Extraction ──
            Text("STEP 1: NEWSPAGE STOCK DATA", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
            Spacer(Modifier.height(8.dp))

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    // Distributor dropdown
                    var expanded by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(
                        expanded = expanded,
                        onExpandedChange = { expanded = !expanded },
                    ) {
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

                    // NP User ID (read-only from DB)
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

                    Spacer(Modifier.height(16.dp))

                    Button(
                        onClick = { viewModel.startExtract() },
                        modifier = Modifier.fillMaxWidth().height(44.dp),
                        enabled = !state.extracting && !state.executing,
                        colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
                    ) {
                        if (state.extracting) {
                            CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Extracting...", fontWeight = FontWeight.Bold)
                        } else if (state.extractDone) {
                            Text("Extracted \u2713", fontWeight = FontWeight.Bold)
                        } else {
                            Text("Step 1: Extract Stock from Newspage", fontWeight = FontWeight.Bold)
                        }
                    }

                    if (state.extractDone) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            "Extraction complete",
                            fontSize = 12.sp, color = BrandSuccess, fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }

            Spacer(Modifier.height(20.dp))

            // ── Step 2: Compare with Distributor File ──
            if (state.extractDone) {
                Text("STEP 2: COMPARE WITH DISTRIBUTOR", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
                Spacer(Modifier.height(8.dp))

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        // File picker
                        val filePicker = rememberLauncherForActivityResult(
                            ActivityResultContracts.GetContent()
                        ) { uri: Uri? ->
                            uri?.let {
                                val name = uri.lastPathSegment?.substringAfterLast('/') ?: "file.xlsx"
                                viewModel.setDistFileUri(it, name)
                            }
                        }

                        OutlinedButton(
                            onClick = { filePicker.launch("*/*") },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(
                                if (state.distFileName.isNotEmpty()) "\uD83D\uDCC4 ${state.distFileName}"
                                else "Upload Distributor Stock File (.csv/.xlsx)"
                            )
                        }

                        Spacer(Modifier.height(16.dp))
                        Text("Column Mapping", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(8.dp))

                        // NP Column mapping
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedTextField(
                                value = state.skuColNp,
                                onValueChange = viewModel::setSkuColNp,
                                label = { Text("SKU (NP)") },
                                modifier = Modifier.weight(1f),
                                textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                            )
                            OutlinedTextField(
                                value = state.descColNp,
                                onValueChange = viewModel::setDescColNp,
                                label = { Text("Desc (NP)") },
                                modifier = Modifier.weight(1f),
                                textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                            )
                        }
                        Spacer(Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedTextField(
                                value = state.qtyColNp,
                                onValueChange = viewModel::setQtyColNp,
                                label = { Text("Qty (NP)") },
                                modifier = Modifier.weight(1f),
                                textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                            )
                            OutlinedTextField(
                                value = state.skuColDist,
                                onValueChange = viewModel::setSkuColDist,
                                label = { Text("SKU (Dist)") },
                                modifier = Modifier.weight(1f),
                                textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                            )
                        }
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = state.qtyColDist,
                            onValueChange = viewModel::setQtyColDist,
                            label = { Text("Qty (Dist)") },
                            modifier = Modifier.fillMaxWidth(0.5f),
                            textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                        )

                        Spacer(Modifier.height(16.dp))

                        Button(
                            onClick = { viewModel.startCompare() },
                            modifier = Modifier.fillMaxWidth().height(44.dp),
                            enabled = !state.comparing && state.distFileUri != null,
                            colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
                        ) {
                            if (state.comparing) {
                                CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                                Spacer(Modifier.width(8.dp))
                                Text("Comparing...", fontWeight = FontWeight.Bold)
                            } else {
                                Text("Step 2: Start Automated Comparison", fontWeight = FontWeight.Bold)
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

                // Match/Mismatch metric cards
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = BrandSuccess.copy(alpha = 0.1f)),
                    ) {
                        Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Match", fontSize = 12.sp, color = BrandSuccess, fontWeight = FontWeight.SemiBold)
                            Text("${state.matchCount}", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = BrandSuccess)
                        }
                    }
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = BrandError.copy(alpha = 0.1f)),
                    ) {
                        Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Difference", fontSize = 12.sp, color = BrandError, fontWeight = FontWeight.SemiBold)
                            Text("${state.mismatchCount}", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = BrandError)
                        }
                    }
                }

                Spacer(Modifier.height(12.dp))

                // Mismatch table
                if (state.mismatchRows.isNotEmpty()) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Mismatched SKUs", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                            Spacer(Modifier.height(8.dp))

                            // Header
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text("SKU", fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(2f))
                                Text("NP", fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                                Text("Dist", fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                                Text("Diff", fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            }
                            Divider()

                            // Rows (show up to 50)
                            state.mismatchRows.take(50).forEach { row ->
                                Row(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                ) {
                                    Text("${row["sku"]}", fontSize = 10.sp, modifier = Modifier.weight(2f), maxLines = 1)
                                    Text("${row["newspage"]}", fontSize = 10.sp, modifier = Modifier.weight(1f))
                                    Text("${row["distributor"]}", fontSize = 10.sp, modifier = Modifier.weight(1f))
                                    val selisih = (row["selisih"] as? Number)?.toFloat() ?: 0f
                                    Text(
                                        "${selisih.toInt()}", fontSize = 10.sp, modifier = Modifier.weight(1f),
                                        color = if (selisih < 0) BrandError else BrandSuccess,
                                    )
                                }
                            }

                            if (state.mismatchRows.size > 50) {
                                Text("...and ${state.mismatchRows.size - 50} more", fontSize = 10.sp, color = BrandTextMuted)
                            }
                        }
                    }
                }

                if (state.mismatchCount > 0) {
                    Spacer(Modifier.height(16.dp))

                    // ── Step 3: Execute ──
                    Text("STEP 3: EXECUTE ADJUSTMENT", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = BrandBlue)
                    Spacer(Modifier.height(8.dp))

                    Button(
                        onClick = { viewModel.startExecute() },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        enabled = !state.executing && !state.executeDone,
                        colors = ButtonDefaults.buttonColors(containerColor = BrandError),
                    ) {
                        if (state.executing) {
                            CircularProgressIndicator(Modifier.size(20.dp), Color.White, 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Executing (${state.progressCurrent}/${state.progressTotal})", fontWeight = FontWeight.Bold)
                        } else if (state.executeDone) {
                            Text("Adjustment Complete \u2713", fontWeight = FontWeight.Bold)
                        } else {
                            Text("EXECUTE (${state.mismatchCount} SKU)", fontWeight = FontWeight.Bold)
                        }
                    }

                    if (state.executing) {
                        Spacer(Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = state.progress,
                            modifier = Modifier.fillMaxWidth().height(6.dp),
                        )
                    }
                } else if (state.compareDone) {
                    Spacer(Modifier.height(16.dp))
                    Card(
                        colors = CardDefaults.cardColors(containerColor = BrandSuccess.copy(alpha = 0.1f)),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            "All SKUs matched! No adjustment needed.",
                            color = BrandSuccess, fontWeight = FontWeight.SemiBold,
                            modifier = Modifier.padding(16.dp),
                        )
                    }
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
